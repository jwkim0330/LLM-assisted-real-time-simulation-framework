import ast
import json
import logging
import math
import os
import queue
import select
import threading
import time

import pandas as pd
import plotly.graph_objects as go
import psycopg2
import psycopg2.extensions
from dotenv import load_dotenv
from flask import Flask, Response, jsonify, request

load_dotenv()

logging.basicConfig(
    level=os.environ.get('LOG_LEVEL', 'INFO'),
    format='%(asctime)s [%(levelname)s] %(message)s',
)
logger = logging.getLogger(__name__)

MAPBOX_TOKEN = os.environ.get('MAPBOX_TOKEN', '')
if not MAPBOX_TOKEN:
    logger.warning('MAPBOX_TOKEN is not set; map tiles will not render.')

DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'port': int(os.environ.get('DB_PORT', '5432')),
    'dbname': os.environ.get('DB_NAME', 'test_drt'),
    'user': os.environ.get('DB_USER', ''),
    'password': os.environ.get('DB_PASSWORD', ''),
}
FLASK_HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
FLASK_PORT = int(os.environ.get('FLASK_PORT', '8050'))

SELECTED_SHUTTLE_ID = None
SELECTED_PASSENGER_ID = None
PASSENGER_TRIP_ENDED = False

binding_df = pd.read_csv('node_coordinates.csv', encoding='utf-8', dtype={'id': str})
binding_df['id'] = binding_df['id'].str.strip()
binding = {row['id']: (row['lat'], row['lon']) for _, row in binding_df.iterrows()}
padding_width = max(len(k) for k in binding.keys())
 
with open('map_graph_with_vectors.json', encoding='utf-8') as f:
    graph = json.load(f)
link_time = {}
for link in graph['links']:
    s, t, sec = link['source'], link['target'], link['time']
    link_time[(s, t)] = sec
    link_time[(t, s)] = sec

current_cur_path = []
current_cur_node = None
current_cur_dst = []

fig = go.Figure()
fig.update_layout(
    mapbox_style='carto-positron',
    mapbox_center={'lat': 37.3033506336632, 'lon': 126.84309728110661},
    mapbox_zoom=14,
    margin={'l':0, 'r':0, 't':0, 'b':0},
    showlegend=False
)

color_list = ['red','blue','green','orange','purple','brown','pink','olive','cyan']
colors = {}
next_color = 0
shuttles = {}
last_time = 0.0

recent_boarding_latlon = {}

def fetch_new_rows():
    global last_time
    cursor.execute(
        """
        SELECT currenttime::double precision AS currenttime,
               shuttle_id, cur_node, cur_path, cur_dst
        FROM vehicle_kpi
        WHERE currenttime::double precision > %s
        ORDER BY currenttime::double precision
        """, (last_time,)
    )
    rows = cursor.fetchall()
    if rows:
        last_time = rows[-1][0]
    return rows

def parse_path(cur_path):
    try:
        nodes = ast.literal_eval(cur_path)
        if isinstance(nodes, (list, tuple)):
            return [str(n) for n in nodes]
    except Exception:
        pass
    return cur_path.split('-')

def parse_cur_dst(cur_dst_raw):
    if isinstance(cur_dst_raw, str):
        try:
            dst_list = ast.literal_eval(cur_dst_raw)
        except Exception:
            dst_list = []
    elif isinstance(cur_dst_raw, list):
        dst_list = cur_dst_raw
    else:
        dst_list = []
    result = []
    for item in dst_list:
        if isinstance(item, (list, tuple)) and len(item) >= 3:
            result.append((str(item[0]), str(item[1]), str(item[2])))
    return result

def get_coordinates(cur_node: str):
    for k in (cur_node.zfill(padding_width), cur_node.lstrip('0'), cur_node):
        if k in binding:
            return binding[k]
    raise KeyError(f"No binding for node '{cur_node}'")

def get_popup_status_and_message(cur_node, cur_path, cur_dst, link_time):
    boarding_node, dropping_node = None, None
    for n, t, pid in cur_dst:
        if t.upper() == 'BOARDING' and boarding_node is None:
            boarding_node = n
        if t.upper() == 'DROPPING' and dropping_node is None:
            dropping_node = n
    try: node_idx = cur_path.index(cur_node)
    except: node_idx = 0
    try: boarding_idx = cur_path.index(boarding_node) if boarding_node else -1
    except: boarding_idx = -1
    try: dropping_idx = cur_path.index(dropping_node) if dropping_node else -1
    except: dropping_idx = -1

    if boarding_node and node_idx < boarding_idx:
        time_sec = 0
        for i in range(node_idx, boarding_idx):
            s, t = cur_path[i], cur_path[i+1]
            time_sec += link_time.get((s, t), link_time.get((t, s), 0))
        minutes = max(1, round(time_sec / 60))
        if boarding_idx - node_idx <= 2:
            return "Vehicle arriving soon. Please get ready to board.", None
        else:
            return f"Boarding in {minutes} min", minutes
    if boarding_node and cur_node == boarding_node:
        return "Please board the vehicle", None
    if dropping_node and node_idx < dropping_idx:
        time_sec = 0
        for i in range(node_idx, dropping_idx):
            s, t = cur_path[i], cur_path[i+1]
            time_sec += link_time.get((s, t), link_time.get((t, s), 0))
        minutes = max(1, round(time_sec / 60))
        if dropping_idx - node_idx <= 2:
            return "Arriving at destination soon", None
        else:
            return f"Arriving in {minutes} min", minutes
    if dropping_node and cur_node == dropping_node:
        return "You have arrived at your destination", None
    return "", None

def db_listener():
    global next_color, current_cur_path, current_cur_node, current_cur_dst, PASSENGER_TRIP_ENDED
    while True:
        if select.select([conn], [], [], None)[0]:
            conn.poll()
            while conn.notifies:
                conn.notifies.pop(0)
                if SELECTED_SHUTTLE_ID is not None and not PASSENGER_TRIP_ENDED:
                    for _, shuttle_id, cur_node, cur_path, cur_dst in fetch_new_rows():
                        cur_dst_list = parse_cur_dst(cur_dst)
                        passenger_ids = [pid for n, t, pid in cur_dst_list if t.upper() in ["BOARDING", "DROPPING"]]
                        if (shuttle_id != SELECTED_SHUTTLE_ID or
                            (SELECTED_PASSENGER_ID is not None and SELECTED_PASSENGER_ID not in passenger_ids)):
                            continue
                        current_cur_path = parse_path(cur_path)
                        current_cur_node = str(cur_node)
                        current_cur_dst = cur_dst_list
                        for n, t, pid in cur_dst_list:
                            if t.upper() == "DROPPING" and current_cur_node == n and pid == SELECTED_PASSENGER_ID:
                                PASSENGER_TRIP_ENDED = True
                        if shuttle_id not in colors:
                            colors[shuttle_id] = color_list[next_color % len(color_list)]
                            next_color += 1
                        color = colors[shuttle_id]
                        try:
                            lat, lon = get_coordinates(cur_node)
                        except KeyError:
                            continue
                        if shuttle_id not in shuttles:
                            fig.add_trace(go.Scattermapbox(
                                lat=[lat], lon=[lon], mode='markers+text',
                                marker={'size':14, 'color':color},
                                text=[shuttle_id], textposition='top center',
                                name=f"{shuttle_id}_pos"
                            ))
                            pos_idx = len(fig.data) - 1
                            coords = []
                            for n in current_cur_path:
                                try:
                                    coords.append(get_coordinates(n))
                                except KeyError:
                                    pass
                            if coords:
                                lats, lons = zip(*coords)
                                fig.add_trace(go.Scattermapbox(
                                    lat=list(lats), lon=list(lons), mode='lines',
                                    line={'width':3, 'color':'blue'},
                                    name=f"{shuttle_id}_path"
                                ))
                                path_idx = len(fig.data) - 1
                            else:
                                path_idx = None
                            shuttles[shuttle_id] = {'cur_node':cur_node,'pos_idx':pos_idx,'path_idx':path_idx}
                        else:
                            info = shuttles[shuttle_id]
                            if info['cur_node'] != cur_node:
                                fig.data[info['pos_idx']].lat = [lat]
                                fig.data[info['pos_idx']].lon = [lon]
                                info['cur_node'] = cur_node
                            if info['path_idx'] is not None:
                                coords = []
                                for n in current_cur_path:
                                    try:
                                        coords.append(get_coordinates(n))
                                    except KeyError:
                                        pass
                                if coords:
                                    lats, lons = zip(*coords)
                                    fig.data[info['path_idx']].lat = list(lats)
                                    fig.data[info['path_idx']].lon = list(lons)
                for q in clients:
                    q.put('data: update\n\n')
        time.sleep(1)

app = Flask(__name__)
clients = []

@app.route('/stream')
def stream():
    def event_stream(q):
        try:
            while True:
                yield q.get()
        except GeneratorExit:
            clients.remove(q)
    q = queue.Queue()
    clients.append(q)
    return Response(event_stream(q), mimetype='text/event-stream')

@app.route('/data')
def data():
    js = fig.to_dict()
    total_sec = 0
    link_time_list = []
    # --------------------------------------------------------
    boarding_node, dropping_node = None, None
    boarding_pid, dropping_pid = None, None
    for n, t, pid in current_cur_dst:
        if t.upper() == 'BOARDING' and boarding_node is None:
            boarding_node = n
            boarding_pid = pid
        if t.upper() == 'DROPPING' and dropping_node is None:
            dropping_node = n
            dropping_pid = pid

    destIdx = -1
    if current_cur_path and dropping_node:
        try:
            destIdx = current_cur_path.index(dropping_node)
        except Exception:
            destIdx = -1

    boarding_coords = None
    dropping_coords = None
    try:
        if boarding_node:
            if boarding_node not in binding and boarding_node in recent_boarding_latlon:
                binding[boarding_node] = recent_boarding_latlon[boarding_node]
            boarding_coords = get_coordinates(boarding_node)
    except Exception:
        boarding_coords = None
    try:
        if dropping_node:
            dropping_coords = get_coordinates(dropping_node)
    except Exception:
        dropping_coords = None

    if current_cur_path and destIdx >= 0:
        for a, b in zip(current_cur_path, current_cur_path[1:destIdx+1]):
            t = link_time.get((a, b), link_time.get((b, a), 0))
            total_sec += t
            link_time_list.append(t)
        eta_min = math.ceil(total_sec / 60)
    else:
        link_time_list = []
        eta_min = None

    popup_message, popup_minutes = get_popup_status_and_message(
        current_cur_node, current_cur_path, current_cur_dst, link_time
    )
    return jsonify(
        data=js['data'], layout=js['layout'], eta=eta_min,
        boarding_coords=boarding_coords,
        dropping_coords=dropping_coords if destIdx >= 0 else None,
        current_cur_node=current_cur_node,
        current_cur_path=current_cur_path,
        current_cur_dst=current_cur_dst,
        boarding_pid=boarding_pid,
        dropping_pid=dropping_pid,
        popup_message=popup_message,
        link_time_list=link_time_list if destIdx >= 0 else [],
        trip_ended=PASSENGER_TRIP_ENDED
    )

@app.route('/')
def index():
    return _INDEX_HTML.replace('__MAPBOX_TOKEN__', MAPBOX_TOKEN)


_INDEX_HTML = '''
<!DOCTYPE html>
<html>
<head>
  <meta charset='utf-8'/>
  <title>2D Real-time Shuttle Map</title>
  <meta name='viewport' content='width=device-width,initial-scale=1'/>
  <link href="https://api.mapbox.com/mapbox-gl-js/v2.14.1/mapbox-gl.css" rel="stylesheet">
  <script src="https://api.mapbox.com/mapbox-gl-js/v2.14.1/mapbox-gl.js"></script>
  <style>
    html, body {margin:0; padding:0; height:100%;}
    #map {position:absolute; top:0; bottom:0; width:100%;}
    .eta-popup {
      font-family: 'Pretendard', Pretendard, 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
      font-weight: 600;
      font-size: 1.12em;
      color: #222;
      background: #fff;
      border-radius: 15px;
      box-shadow: 0 3px 14px #0002;
      padding: 10px 18px 8px 18px;
      border: none;
      margin-bottom: 4px;
      text-align: center;
      min-width: 110px;
      max-width: 220px;
      letter-spacing: -0.03em;
      position: relative;
    }
    .eta-popup b {
      color: #0080ff;
      font-size: 1.32em;
      font-family: 'Pretendard', Pretendard, 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif;
      font-weight: 700;
    }
    .mapboxgl-popup-tip { display: none !important; }
    .mapboxgl-popup-content { border-radius: 15px !important; box-shadow: 0 3px 14px #0002 !important; border: none !important;}
    
        /* Map zoom button styling */
    .mapboxgl-ctrl-bottom-right .mapboxgl-ctrl {
      margin: 20px 16px;
    }
    .mapboxgl-ctrl.mapboxgl-ctrl-group {
      border-radius: 18px !important;
      box-shadow: 0 2px 16px #2221;
      overflow: hidden;
    }
    .mapboxgl-ctrl-group button {
      width: 54px !important;
      height: 54px !important;
      font-size: 2.2em !important;
      border-radius: 0 !important;
      background: #fff;
      border: none !important;
      box-shadow: none !important;
      color: #0080ff !important;
      transition: background 0.2s;
    }
    .mapboxgl-ctrl-group button:hover {
      background: #e6f3ff !important;
    }
    .mapboxgl-ctrl-group button:active {
      background: #cce7ff !important;
    }

    
  </style>
  <link href="https://cdn.jsdelivr.net/npm/pretendard@1.3.7/dist/web/variable/pretendardvariable.css" rel="stylesheet"/>
</head>
<body>
  <div id="map"></div>
  <script>
    const SPEED_MULTIPLIER = 2;
    mapboxgl.accessToken = '__MAPBOX_TOKEN__';

    const map = new mapboxgl.Map({
      container: 'map',
      style: 'mapbox://styles/mapbox/streets-v12',
      center: [126.8431, 37.3034],
      zoom: 16
    });

    let boardingMarker = null;
    let droppingMarker = null;
    let vehiclePopup = null;
    let vehicleMarkerPos = null;
    let animationFrame = null;
    let tripEnded = false;
    let shuttleMarker = null;
    let firstMapCentered = false;


    // Anti-flicker: cache path coordinates
    let prevRenderedPathLon = [], prevRenderedPathLat = [];
    let prevCurNode = null;
    let prevCurPath = null;
    let prevIdx = null;
    let isAnimating = false;
    let curAnimatedIdx = null;
    let lastAnimatedPos = null;
    let latestDestIdx = null;
    let latestPath = null;
    let latestShuttlePos = null;

    

    function round7(x) { return Math.round(x * 1e7) / 1e7; }
    function arraysAlmostEqual(a, b, eps=1e-7) {
      if (!a || !b || a.length !== b.length) return false;
      for (let i=0; i<a.length; ++i)
        if (Math.abs(a[i]-b[i]) > eps) return false;
      return true;
    }

    function createCarMarker() {
      const carDiv = document.createElement('div');
      carDiv.style.width = "44px";
      carDiv.style.height = "44px";
      carDiv.style.background = "none";
      carDiv.style.borderRadius = "50%";
      carDiv.style.overflow = "visible";
      carDiv.innerHTML = `
        <svg width="40" height="40" viewBox="0 0 60 60">
          <ellipse cx="30" cy="35" rx="15" ry="20" fill="#0080ff" />
          <rect x="20" y="12" width="20" height="25" rx="8" fill="#fff"/>
          <ellipse cx="30" cy="45" rx="8" ry="7" fill="#eee"/>
          <rect x="24" y="17" width="12" height="12" rx="5" fill="#d9e5fc"/>
        </svg>`;
      return carDiv;
    }

    map.on('load', () => {
      map.addSource('path', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
      map.addLayer({
        id: 'path-layer',
        type: 'line',
        source: 'path',
        paint: { 'line-width': 5, 'line-color': '#0080ff' }
      });
      map.addControl(new mapboxgl.NavigationControl({ showCompass: false }), 'bottom-right');
      
      setTimeout(() => {
        const navControl = document.querySelector('.mapboxgl-ctrl-bottom-right .mapboxgl-ctrl-group');
        if (navControl) {
          const carBtn = document.createElement('button');
          carBtn.type = 'button';
          carBtn.className = 'mapboxgl-ctrl-icon car-center-btn';
          carBtn.style.display = 'flex';
          carBtn.style.alignItems = 'center';
          carBtn.style.justifyContent = 'center';
          carBtn.style.width = '54px';
          carBtn.style.height = '54px';
          carBtn.style.borderRadius = '0';
          carBtn.style.background = '#fff';
          carBtn.style.border = 'none';
          carBtn.style.outline = 'none';
          carBtn.style.boxShadow = 'none';
          carBtn.title = 'Center on vehicle';

          carBtn.innerHTML = `
            <svg width="28" height="28" viewBox="0 0 32 32" fill="none">
              <rect x="5" y="11" width="22" height="8" rx="3.5" fill="#0080ff"/>
              <rect x="9" y="8" width="14" height="7" rx="2" fill="#d9e5fc"/>
              <circle cx="9" cy="23" r="3" fill="#555"/>
              <circle cx="23" cy="23" r="3" fill="#555"/>
            </svg>
          `;

          carBtn.onclick = function() {
            if (latestShuttlePos && !isNaN(latestShuttlePos[0]) && !isNaN(latestShuttlePos[1])) {
                map.setCenter(latestShuttlePos);
            }
          };

          navControl.insertBefore(carBtn, navControl.firstChild);
        }
      }, 500);
      
      updateMap();
      setInterval(updateMap, 1500);
    });

    function stylePopup(msg) {
      if (!msg) return '';
      return msg.replace(/(\d+)/g, "<b>$1</b>");
    }

    function animateVehicle(lastPos, nextPos, duration, idx, destIdx, path) {
      isAnimating = true;
      const start = performance.now();
      function step(now) {
        if (tripEnded) return;
        const elapsed = (now - start) / 1000.0;
        let t = Math.min(elapsed / duration, 1.0);
        const lon = lastPos[0] + (nextPos[0] - lastPos[0]) * t;
        const lat = lastPos[1] + (nextPos[1] - lastPos[1]) * t;
        lastAnimatedPos = [lon, lat];

        // Render path only up to destination index
        let pathLon = path.lon.slice(0, destIdx+1);
        let pathLat = path.lat.slice(0, destIdx+1);
        let segLons = [round7(lon)], segLats = [round7(lat)];
        for (let i = idx+1; i <= destIdx; i++) {
          if (typeof pathLon[i] !== 'undefined' && typeof pathLat[i] !== 'undefined') {
            segLons.push(round7(pathLon[i]));
            segLats.push(round7(pathLat[i]));
          }
        }
        if (!arraysAlmostEqual(segLons, prevRenderedPathLon) || !arraysAlmostEqual(segLats, prevRenderedPathLat)) {
          prevRenderedPathLon = segLons.slice();
          prevRenderedPathLat = segLats.slice();
          map.getSource('path').setData({
            type: 'FeatureCollection',
            features: segLons.length > 1 ? [{
              type: 'Feature',
              geometry: { type: 'LineString', coordinates: segLons.map((lon, i) => [lon, segLats[i]]) }
            }] : []
          });
        }

        if (shuttleMarker) shuttleMarker.setLngLat([lon, lat]);
        if (vehiclePopup) vehiclePopup.setLngLat([lon, lat]);
        if (t < 1.0) animationFrame = requestAnimationFrame(step);
        else {
          lastAnimatedPos = [nextPos[0], nextPos[1]];
          isAnimating = false;
        }
      }
      animationFrame = requestAnimationFrame(step);
    }

    function updateMap() {
      fetch('/data').then(r => r.json()).then(resp => {
        tripEnded = resp.trip_ended || false;

        // Boarding / dropping markers
        if (resp.boarding_coords) {
          const [lat, lon] = resp.boarding_coords;
          if (!boardingMarker) {
            boardingMarker = new mapboxgl.Marker({ color: 'blue' })
              .setLngLat([lon, lat]).addTo(map);
          } else {
            boardingMarker.setLngLat([lon, lat]);
          }
        } else if (boardingMarker) { boardingMarker.remove(); boardingMarker = null; }
        if (resp.dropping_coords) {
          const [lat, lon] = resp.dropping_coords;
          if (!droppingMarker) {
            droppingMarker = new mapboxgl.Marker({ color: 'red' })
              .setLngLat([lon, lat]).addTo(map);
          } else {
            droppingMarker.setLngLat([lon, lat]);
          }
        } else if (droppingMarker) { droppingMarker.remove(); droppingMarker = null; }

        // Blue path (vehicle position -> destination node)
        const plotlyData = resp.data;
        let pos = null, path = null;
        for (const trace of plotlyData) {
          if (trace.name && trace.name.endsWith('_pos')) pos = { lon: trace.lon[0], lat: trace.lat[0] };
          if (trace.name && trace.name.endsWith('_path')) path = { lon: trace.lon, lat: trace.lat };
          if (pos) {latestShuttlePos = [parseFloat(pos.lon), parseFloat(pos.lat)];}

        }
        let destIdx = -1;
        if (resp.current_cur_path && resp.current_cur_dst) {
          let cur_path = resp.current_cur_path;
          let dst = resp.current_cur_dst;
          let destNode = null;
          for (const v of dst) {
            if (v[1] && v[1].toUpperCase() === "DROPPING") {
              destNode = v[0];
              break;
            }
          }
          if (cur_path && destNode) {
            destIdx = cur_path.indexOf(destNode);
            latestDestIdx = destIdx;
            latestPath = path;
          }
        }

        if (destIdx < 0) {
          prevRenderedPathLon = [];
          prevRenderedPathLat = [];
          if (map.getSource('path')) {
            map.getSource('path').setData({
              type: 'FeatureCollection',
              features: []
            });
          }
        }

        let markerPos = null;
        if (lastAnimatedPos && isAnimating === false) {
          markerPos = lastAnimatedPos;
        } else if (pos) {
          markerPos = [parseFloat(pos.lon), parseFloat(pos.lat)];
        }
        if (!firstMapCentered && markerPos) {
        map.setCenter(markerPos);
        firstMapCentered = true;
        }

        // Path up to destination only
        if (markerPos && path && resp.current_cur_path && destIdx >= 0) {
          let cur_path = resp.current_cur_path;
          let idx = cur_path.indexOf(resp.current_cur_node);

          let pathLon = path.lon.slice(0, destIdx+1);
          let pathLat = path.lat.slice(0, destIdx+1);

          let segLons = [round7(markerPos[0])], segLats = [round7(markerPos[1])];
          for (let i = idx+1; i <= destIdx; i++) {
            if (typeof pathLon[i] !== 'undefined' && typeof pathLat[i] !== 'undefined') {
              segLons.push(round7(pathLon[i]));
              segLats.push(round7(pathLat[i]));
            }
          }
          if (!arraysAlmostEqual(segLons, prevRenderedPathLon) || !arraysAlmostEqual(segLats, prevRenderedPathLat)) {
            prevRenderedPathLon = segLons.slice();
            prevRenderedPathLat = segLats.slice();
            map.getSource('path').setData({
              type: 'FeatureCollection',
              features: segLons.length > 1 ? [{
                type: 'Feature',
                geometry: { type: 'LineString', coordinates: segLons.map((lon, i) => [lon, segLats[i]]) }
              }] : []
            });
          }
        }

        // Vehicle marker
        if (markerPos) {
          if (!shuttleMarker) {
            shuttleMarker = new mapboxgl.Marker({ element: createCarMarker(), anchor: 'center' })
              .setLngLat(markerPos).addTo(map);
          } else {
            shuttleMarker.setLngLat(markerPos);
          }
        } else if (shuttleMarker) {
          shuttleMarker.remove();
          shuttleMarker = null;
        }

        // Node-to-node animation
        if (!tripEnded && resp.current_cur_path && resp.current_cur_node && path && resp.link_time_list && destIdx >= 0) {
          const cur_path = resp.current_cur_path;
          const cur_node = resp.current_cur_node;
          const idx = cur_path.indexOf(cur_node);

          let shouldAnimate = false;
          if (prevCurPath === null || prevCurNode === null ||
              prevCurPath.join() != cur_path.join() || prevCurNode !== cur_node || prevIdx !== idx) {
            shouldAnimate = true;
          }

          if (shouldAnimate && idx >= 0 && idx < destIdx && pos) {
            const lastPos = [parseFloat(pos.lon), parseFloat(pos.lat)];
            const nextPos = [
              parseFloat(path.lon[idx + 1]),
              parseFloat(path.lat[idx + 1])
            ];
            const linkTimeList = resp.link_time_list || [];
            let duration = 1.0;
            if (linkTimeList.length > idx) duration = linkTimeList[idx] / SPEED_MULTIPLIER;
            if (animationFrame) cancelAnimationFrame(animationFrame);
            curAnimatedIdx = idx;
            animateVehicle(lastPos, nextPos, duration, idx, destIdx, path);

            prevCurNode = cur_node;
            prevCurPath = cur_path.slice();
            prevIdx = idx;
          }
        }

        // Popup always anchored at markerPos
        if (resp.popup_message && markerPos) {
          if (!vehiclePopup) {
            vehiclePopup = new mapboxgl.Popup({
              closeButton:false, closeOnClick:false, offset: [0, -30]
            })
              .setLngLat(markerPos)
              .setHTML(`<div class="eta-popup">${stylePopup(resp.popup_message)}</div>`)
              .addTo(map);
            vehicleMarkerPos = markerPos;
          } else {
            vehiclePopup.setLngLat(markerPos)
              .setHTML(`<div class="eta-popup">${stylePopup(resp.popup_message)}</div>`);
            vehicleMarkerPos = markerPos;
          }
        } else if (vehiclePopup) {
          vehiclePopup.remove(); vehiclePopup = null; vehicleMarkerPos = null;
        }
      });
    }
  </script>
</body>
</html>
'''

@app.route('/shuttle_data', methods=['POST'])
def update():
    global SELECTED_SHUTTLE_ID, SELECTED_PASSENGER_ID, last_time, shuttles, fig, current_cur_path, next_color, colors, PASSENGER_TRIP_ENDED
    global recent_boarding_latlon
    payload = request.get_json()

    logger.info(
        'Received payload: shuttle_id=%s passenger_id=%s',
        payload.get('shuttle_id'), payload.get('passengerId'),
    )
    logger.debug('Departure: %s (%s, %s)',
                 payload.get('Departure'),
                 payload.get('Departure_Latitude'),
                 payload.get('Departure_Longitude'))
    logger.debug('Destination: %s (%s, %s)',
                 payload.get('Destination'),
                 payload.get('Destination_Latitude'),
                 payload.get('Destination_Longitude'))
    if 'cur_dst' in payload:
        logger.debug('cur_dst: %s', payload.get('cur_dst'))

    new_shuttle_id = payload['shuttle_id']
    new_passenger_id = str(payload.get('passengerId', ''))

    if SELECTED_SHUTTLE_ID != new_shuttle_id or SELECTED_PASSENGER_ID != new_passenger_id:
        logger.info('Selection changed: shuttle=%s passenger=%s', new_shuttle_id, new_passenger_id)
        SELECTED_SHUTTLE_ID = new_shuttle_id
        SELECTED_PASSENGER_ID = new_passenger_id
        PASSENGER_TRIP_ENDED = False
        fig.data = []
        shuttles.clear()
        current_cur_path = []
        last_time = 0.0
        colors = {}
        next_color = 0
    
    boarding_node = None
    if 'cur_dst' in payload:
        try:
            dst_list = ast.literal_eval(payload['cur_dst'])
        except Exception:
            dst_list = []
        for item in dst_list:
            if isinstance(item, (list, tuple)) and len(item) >= 2:
                if str(item[1]).upper() == 'BOARDING':
                    boarding_node = str(item[0])
                    break
    
    if boarding_node and 'Departure_Latitude' in payload and 'Departure_Longitude' in payload:
        recent_boarding_latlon[boarding_node] = (payload['Departure_Latitude'], payload['Departure_Longitude'])
        binding[boarding_node] = (payload['Departure_Latitude'], payload['Departure_Longitude'])
        logger.info('Bound boarding node %s -> (%s, %s)',
                    boarding_node,
                    payload['Departure_Latitude'],
                    payload['Departure_Longitude'])

    msg = f"data: {json.dumps(payload)}\n\n"
    for q in clients:
        q.put(msg)

    logger.debug('Payload broadcast to %d client(s)', len(clients))
    return '', 204


if __name__ == '__main__':
    try:
        logger.info('Connecting to database %s@%s:%s/%s',
                    DB_CONFIG['user'], DB_CONFIG['host'],
                    DB_CONFIG['port'], DB_CONFIG['dbname'])
        conn = psycopg2.connect(**DB_CONFIG)
        logger.info('Database connection established')

        conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()

        cursor.execute("LISTEN new_vehicle;")
        logger.info('Listening on channel: new_vehicle')

        fig.data = []
        shuttles.clear()
        last_time = 0.0

        threading.Thread(target=db_listener, daemon=True).start()
        logger.info('Starting server on %s:%d', FLASK_HOST, FLASK_PORT)
        app.run(host=FLASK_HOST, port=FLASK_PORT)

    except psycopg2.OperationalError as e:
        logger.error('Database connection failed: %s', e)
        logger.error('Check: PostgreSQL is running, DB_NAME/DB_USER/DB_PASSWORD/DB_PORT in .env are correct')
    except Exception as e:
        logger.exception('Unexpected error: %s', e)
