class Logger:
    def __init__(self):
        self.message = ''

    # Simple Message
    def msg_log(self, message):
        msg = '\x1b[0;37;40m' +  str(message) + '\x1b[0;37;40m'
        print(f'{msg}')
    
    # Init Message
    def init_log(self, message):
        msg = '\x1b[0;34;40m' + 'Bot Initialization: ' +  str(message) + '\x1b[0;37;40m'
        print(f'{msg}')

    # Status Message
    def status_log(self, message):
        msg = '\x1b[0;36;40m' + 'Bot Status: ' + str(message) + '\x1b[0;37;40m'
        print(f'{msg}')
    
    # Warning Message
    def warning_log(self, message):
        msg = '\x1b[0;33;40m' + 'Bot Warning: ' + str(message) + '\x1b[0;37;40m'
        print(f'{msg}')

    # Error Message
    def error_log(self, message):
        msg = '\x1b[0;31;40m' + 'Bot Error: ' + str(message) + '\x1b[0;37;40m'
        print(f'{msg}')