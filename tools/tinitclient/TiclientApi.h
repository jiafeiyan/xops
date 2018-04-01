// TiclientApi.h: interface for the CTiclientApi class.
//
//////////////////////////////////////////////////////////////////////

#if !defined(AFX_TICLIENTAPI_H__A4943292_88D2_497D_9B07_8AD6764B451D__INCLUDED_)
#define AFX_TICLIENTAPI_H__A4943292_88D2_497D_9B07_8AD6764B451D__INCLUDED_

#if _MSC_VER > 1000
#pragma once
#endif // _MSC_VER > 1000

const int ACT_SUCCESS			= 0;
const int ACT_ERR_TIMEOUT		= -1;
const int ACT_ERR_REQ_SEND		= -2;
const int ACT_ERR_RESPONSE		= -3;

///活跃
#define TIC_ES_Active '1'
///不活跃
#define TIC_ES_NonActive '2'

///不活跃
#define TIC_SS_NonActive '1'
///启动
#define TIC_SS_Startup '2'
///操作
#define TIC_SS_Operating '3'
///结算
#define TIC_SS_Settlement '4'
///结算完成
#define TIC_SS_SettlementFinished '5'
///未同步
#define TIC_EDS_Asynchronous '1'
///同步中
#define TIC_EDS_Synchronizing '2'
///已同步
#define TIC_EDS_Synchronized '3'
///未同步
#define TIC_SGDS_Asynchronous '1'
///同步中
#define TIC_SGDS_Synchronizing '2'
///已同步
#define TIC_SGDS_Synchronized '3'


struct TSystemStatus
{
	char TradingDay[9];					//交易日
	char SystemStatus;					//交易所状态
};

struct TDataSyncStatus
{
	char TradingDay[9];					//交易日
	char DataSyncStatus;				//交易所数据同步状态
};

#ifdef ISLIB
#ifdef WIN32
#ifdef LIB_API_EXPORT
#define API_EXPORT __declspec(dllexport)
#else
#define API_EXPORT __declspec(dllimport)
#endif
#else
#define API_EXPORT 
#endif
#else
#define API_EXPORT 
#endif

class API_EXPORT CTiclientApi  
{
public:
	virtual void Release() = 0;

	virtual void RegisterTinit(int nServerID, char *pszFrontAddress) = 0;
	
	virtual void Start() = 0;
	
	virtual int Login(const char *pszUserName, const char *pszParticipantID, 
		const char *pszPassword, const int nTimeOut) = 0;

	virtual int DataSync(const char *pszTradingDay, const int nTimeOut) = 0;

	virtual int QrySystemStatus(TSystemStatus *pSystemStatus, int *pSize, 
		const int nTimeOut) = 0;
	
	virtual int QryDataSyncStatus(TDataSyncStatus *peDataSyncStatus, 
		int *pSize, const int nTimeOut) = 0;
	
	virtual int GetRspErrorID() = 0;
	
	virtual const char *GetRspErrorMsg() = 0;

	static CTiclientApi *CreateTiclientApi();
protected:
	virtual ~CTiclientApi(){};

};

#endif // !defined(AFX_TICLIENTAPI_H__A4943292_88D2_497D_9B07_8AD6764B451D__INCLUDED_)
