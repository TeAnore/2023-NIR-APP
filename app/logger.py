class Logger:
    '''
    def print_format_table():

        #prints table of formatted text format options
        for style in range(8):
            for fg in range(30,38):
                s1 = ''
                for bg in range(40,48):
                    format = ';'.join([str(style), str(fg), str(bg)])
                    s1 += '\x1b[%sm %s \x1b[0m' % (format, format)
                print(s1)
            print('\n')

    print_format_table()
    '''
    # DEvelop Message Purple
    def dev_log(self, message):
        msg = '\x1b[0;35;40m' +  str(message) + '\x1b[0;37;40m'
        print(f'{msg}')

    # Simple Message White
    def msg_log(self, message):
        msg = '\x1b[0;37;40m' +  str(message) + '\x1b[0;37;40m'
        print(f'{msg}')
    
    # Init Message Deep Blue
    def init_log(self, message):
        msg = '\x1b[0;34;40m' + 'Bot Initialization: ' +  str(message) + '\x1b[0;37;40m'
        print(f'{msg}')

    # Status Message Blue
    def status_log(self, message):
        msg = '\x1b[0;36;40m' + 'Bot Status: ' + str(message) + '\x1b[0;37;40m'
        print(f'{msg}')
    
    # Warning Message Yellow
    def warning_log(self, message):
        msg = '\x1b[0;33;40m' + 'Bot Warning: ' + str(message) + '\x1b[0;37;40m'
        print(f'{msg}')

    # Error Message Red
    def error_log(self, message):
        msg = '\x1b[0;31;40m' + 'Bot Error: ' + str(message) + '\x1b[0;37;40m'
        print(f'{msg}')