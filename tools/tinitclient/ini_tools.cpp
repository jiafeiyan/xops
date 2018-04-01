#include <fstream>
#include <string.h>
#include <string>

#include "ini_tools.h"

using namespace std;

IniRepository::IniRepository()
{
    repo = new map<string, map<string, string>>();
};

IniRepository::~IniRepository()
{
    delete repo;
};

void IniRepository::load_ini(const char *ini_file_path)
{
    fstream fis(ini_file_path, ios::in);

    string s;
    string section = "";
    map<string, map<string, string>>::iterator section_ite;
    while (getline(fis, s))
    {
        if (s.find("#") == 0)
        {
            continue;
        }
        else if (s.find("[") == 0)
        {
            section = s.substr(1, s.find("]") - 1);
        }
        else
        {
            int eq_op_pos = s.find("=");
            string key = s.substr(0, eq_op_pos);
            string value = "";
            if (eq_op_pos + 1 < s.length())
            {
                value = s.substr(eq_op_pos + 1);
            }

            section_ite = repo->find(section);
            if(section_ite == repo->end())
            {
                map<string, string> entries;
                entries.insert(pair<string, string>(key, value));
                repo->insert(pair<string, map<string, string>>(section, entries));
            }
            else
            {
                section_ite->second.insert(pair<string, string>(key, value));
            }
        }
    }

    fis.close();
};

void IniRepository::get_string(char *dest, const char *section, const char *key, const char *default_value){
    string t_section = section == NULL ? "" : section;

    map<string, map<string, string>>::iterator section_ite = repo->find(t_section);

    if(section_ite == repo->end())
    {
        strncpy(dest, default_value, strlen(default_value));
    }
    else
    {
        map<string, string>::iterator value_ite = section_ite->second.find(key);

        if(value_ite == section_ite->second.end())
        {
            strncpy(dest, default_value, strlen(default_value));
        }
        else
        {
            strncpy(dest, value_ite->second.c_str(), value_ite->second.length());
        }
    }
};

int IniRepository::get_int(const char *section, const char *key, int default_value)
{
    char string_value[20] = { 0 };
    get_string(string_value, section, key, "");

    if(strlen(string_value) == 0)
    {
        return default_value;
    }
    return atoi(string_value);
};