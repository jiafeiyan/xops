#ifndef __INI_TOOLS_HE
#define __INI_TOOLS_HE
#pragma once

#include <map>

using namespace std;

class IniRepository
{
  public:
    IniRepository();
    ~IniRepository();
  public:
    void load_ini(const char *ini_file_path);

    void get_string(char *dest, const char *section, const char *key, const char *default_value);

    int get_int(const char *section, const char *key, int default_value);

  private:
    map<string, map<string, string>> *repo;
};

#endif