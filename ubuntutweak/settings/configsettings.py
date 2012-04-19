import logging
import ConfigParser

log = logging.getLogger('ConfigSetting')

class RawConfigSetting(object):
    '''Just pass the file path'''
    def __init__(self, path):
        self._type = type

        self._path = path

        self.init_configparser()

    def init_configparser(self):
        self._configparser = ConfigParser.ConfigParser()
        self._configparser.read(self._path)

    def sections(self):
        return self._configparser.sections()

    def options(self, section):
        return self._configparser.options(section)

    def get_value(self, section, option):
        value = self._configparser.get(section, option)
        #TODO deal with list
        if value == 'true':
            return True
        elif value == 'false':
            return False
        elif value.startswith('"') or value.startswith("'"):
            return eval(value)
        else:
            return value

    def is_override_schema(self):
        return self._path.startswith('/usr/share/glib-2.0/schemas/') and self._path.endswith('override')


class ConfigSetting(RawConfigSetting):
    '''Key: /etc/lightdm/lightdm.conf::UserManager#load-users
    '''

    def __init__(self, key=None, default=None, type=None):
        self._path = key.split('::')[0]
        RawConfigSetting.__init__(self, self._path)

        self._type = type

        self._default = default
        self.key = key
        self._section = key.split('::')[1].split('#')[0]
        self._option = key.split('::')[1].split('#')[1]

    def get_value(self):
        try:
            if self._type:
                if self._type == int:
                    getfunc = getattr(self._configparser, 'getint')
                elif self._type == float:
                    getfunc = getattr(self._configparser, 'getfloat')
                elif self._type == bool:
                    getfunc = getattr(self._configparser, 'getboolean')
                else:
                    getfunc = getattr(self._configparser, 'get')

                value = getfunc(self._section, self._option)
            else:
                value = self._configparser.get(self._section, self._option)
        except Exception, e:
            log.error(e)
            value = ''

        if value or self._default:
            return value or self._default
        else:
            if self._type == int:
                return 0
            elif self._type == float:
                return 0.0
            elif self._type == bool:
                return False
            else:
                return ''

    def set_value(self, value):
        if not self._configparser.has_section(self._section):
            self._configparser.add_section(self._section)

        self._configparser.set(self._section, self._option, value)
        with open(self._path, 'wb') as configfile:
            self._configparser.write(configfile)

        self.init_configparser()

    def get_key(self):
        return self.key


class SystemConfigSetting(ConfigSetting):
    def set_value(self, value):
        # Because backend/daemon will use ConfigSetting , proxy represents the
        # daemon, so lazy import the proxy here to avoid backend to call proxy
        from ubuntutweak.policykit.dbusproxy import proxy

        if type(value) == bool:
            if value == True:
                value = 'true'
            elif value == False:
                value = 'false'

        proxy.set_config_setting(self.get_key(), value)

        self.init_configparser()
