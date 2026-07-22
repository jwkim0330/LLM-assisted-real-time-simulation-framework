class Ball():
    
    def __init__(self):
        self.attack_power = 0
        self.rally_count = 0
        self.serve_miss = False
    
    def serve(self, server, attack_power):
        self.attacker = server
        self.attack_power = attack_power
        self.rally_count += 1
        self.serve_miss = False
        self.log(server,
                 'Serve ', 
                 attack_power=attack_power)
    
    def fail_to_serve(self, server):
        self.failed_player = server
        self.serve_miss = True
        self.log(server,
                 'Serve Missed')
        
    def receive(self, receiver, defense_power, attack_power):
        self.attacker = receiver
        self.attack_power = attack_power
        self.rally_count += 1
        self.log(receiver,
                 'Receive', 
                 defense_power=defense_power, 
                 attack_power=attack_power)

    def fail_to_receive(self, receiver, defense_power):
        self.failed_player = receiver
        self.scorer = self.attacker
        self.rally_count += 1
        self.log(receiver,
                 'Failed', 
                 defense_power=defense_power)
    
    def is_serve_miss(self):
        return self.serve_miss
    
    def get_scorer(self):
        return self.scorer
    
    def get_attack_power(self):
        return self.attack_power
    
    def log(self, player, log_type, defense_power=None, attack_power=None):
        str_rally = self.log_formatting('Rally', self.rally_count)
        str_player = self.log_formatting(value=player)
        str_log_type = self.log_formatting(keyword=log_type)
        if defense_power is None:
            str_defense_power = self.log_formatting()
        else:
            str_defense_power = self.log_formatting('Defense', defense_power)
        if attack_power is None:
            str_attack_power = self.log_formatting()
        else:
            str_attack_power = self.log_formatting('Attack', attack_power)
        print(str_rally 
              + str_player 
              + str_log_type 
              + str_defense_power 
              + str_attack_power
              + '|')
    
    @staticmethod
    def log_formatting(keyword=None, value=None):
        if keyword is None and value is None:
            log_str = ''
        elif keyword is None:
            log_str = str(value)
        elif value is None:
            log_str = str(keyword)
        else:
            log_str = str(keyword) + ' : ' + str(value)
        return '| {0:<14}'.format(log_str)