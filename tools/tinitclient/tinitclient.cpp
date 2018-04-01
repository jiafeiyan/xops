#include <iostream>
#include <string.h>

#include "ini_tools.h"
#include "TiclientApi.h"

using namespace std;

int main(int argc, char *argv[])
{
	if (argc > 3 || argc < 2)
	{
		printf("Usage: ./tinitclient trading_day [ini_file] \n");
		exit(-1);
	}

	char ini_file[256] = { 0 };
	if (argc == 3)
	{
		strncpy(ini_file, argv[2], strlen(argv[2]));
	}
	else
	{
		strncpy(ini_file, argv[0], strlen(argv[0]));
		strcat(ini_file, ".ini");
	}
	char *trading_day = argv[1];
	cout << "ini file:" << ini_file << flush << endl;
	cout << "trading day:" << trading_day << flush << endl;

	IniRepository ini_repo;
	ini_repo.load_ini(ini_file);

	char frontAddress[30] = { 0 };
	char user[16] = { 0 };
	char participant[16] = { 0 };
	char password[41] = { 0 };
	ini_repo.get_string(frontAddress, NULL, "FrontAddress", "");
	ini_repo.get_string(user, NULL, "User", "");
	ini_repo.get_string(participant, NULL, "Participant", "");
	ini_repo.get_string(password, NULL, "Password", "");

	cout << "FrontAddress=" << frontAddress << flush << endl;
	cout << "User=" << user << flush << endl;
	cout << "Participant=" << participant << flush << endl;
	cout << "Password=" << password << flush << endl;

	CTiclientApi *ticApi = CTiclientApi::CreateTiclientApi();

	ticApi->RegisterTinit(0, frontAddress);
	ticApi->Start();

	int rtn_code = ticApi->Login(user, participant, password, 30);
	if (ACT_SUCCESS != rtn_code)
	{
		cout << "Login error" << flush << endl;
		ticApi->Release();
		exit(1);
	}

	cout << "Login success" << flush << endl;

	TSystemStatus tss;
	memset(&tss, 0, sizeof(TSystemStatus));
	int psize = sizeof(TSystemStatus);
	rtn_code = ticApi->QrySystemStatus(&tss, &psize, 30);
	if (ACT_SUCCESS != rtn_code)
	{
		cout << "QrySystemStatus error" << flush << endl;
		ticApi->Release();
		exit(1);
	}

	int error_id = ticApi->GetRspErrorID();

	if (error_id != 0) 
	{
		cout << "QrySystemStatus data error:" << tss.TradingDay << "-" << tss.SystemStatus << "-" << ticApi->GetRspErrorMsg() << flush << endl;
		ticApi->Release();
		exit(1);
	}
	cout << "QrySystemStatus success:" << tss.TradingDay << "-" << tss.SystemStatus << flush << endl;

	TDataSyncStatus tdss;
	psize = sizeof(TDataSyncStatus);
	memset(&tdss, 0, sizeof(TDataSyncStatus));
	rtn_code = ticApi->QryDataSyncStatus(&tdss, &psize, 30);
	if (ACT_SUCCESS != rtn_code)
	{
		cout << "QryDataSyncStatus error" << flush << endl;
		ticApi->Release();
		exit(1);
	}

	error_id = ticApi->GetRspErrorID();

	if (error_id != 0 || memcmp(tdss.TradingDay, trading_day, strlen(trading_day)) != 0)
	{
		cout << "QryDataSyncStatus error:" << tdss.TradingDay << "-" << tdss.DataSyncStatus << "-" << ticApi->GetRspErrorMsg() << flush << endl;
		ticApi->Release();
		exit(1);
	}
	cout << "QryDataSyncStatus success:" << tdss.TradingDay << "-" << tdss.DataSyncStatus << flush << endl;
	
	cout << "start datasync......" << flush << endl;
	cout << tdss.TradingDay << flush << endl;
	rtn_code = ticApi->DataSync(tdss.TradingDay, 30);
	if (ACT_SUCCESS != rtn_code)
	{
		cout << "DataSync error" << flush << endl;
		ticApi->Release();
		exit(1);
	}

	cout << "tinit datasync success" << flush << endl;
	ticApi->Release();
};
