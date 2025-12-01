// stdafx.h : 标准系统包含文件的包含文件，
// 或是经常使用但不常更改的
// 特定于项目的包含文件
//

#pragma once

#include "targetver.h"
#include "../../Lib/CHR34XXX_lib.h"
#include <stdio.h>
#include <tchar.h>
// TODO: 在此处引用程序需要的其他头文件


/******************自定义结构体*******************/
//异步协议配置
struct ASYN_FRAMEFORMATST
{
	BYTE HDR;
	BYTE EDR;
	BYTE TailA;
	BYTE TailB;
	BYTE LENR;
	BYTE pt_num;//协议号
	BYTE SumCheckEN;//校验和使能
	BYTE HeadIncluded;//值为1时，表示校验和包含帧起始符，值为0时，表示校验和不包含帧起始符
};

//同步协议配置
struct SYNC_FRAMEFORMATST
{
	BYTE HR[4];
	BYTE ER[4];
	BYTE FrameIDCnt;//帧ID数量
	BYTE FrameIDOrder;//帧ID顺序
	BYTE FrameIDLocation;//帧ID位置
	BYTE LocationAddress;//本地地址
	BYTE SYNCWordCnt;//同步字数量
	BYTE CRCInitVal;//CRC初始值
	BYTE CRCOrder;//CRC初始值
	BYTE ErrFrameEn;//错帧使能
	BYTE SendEdge;//发送边沿
	BYTE RecvEdge;//接收边沿
	BYTE RecvMode;//接收模式
	BYTE AddressTesting;//地址检测
	BYTE CRCTesting;//CRC校验检测
	BYTE SYNCWordTesting;//同步字检测
	BYTE CodeErrTesting;//编码错误检测
	BYTE lackCntTesting;//少数错误检测
};

//协议配置
typedef struct protocolCGF
{
	ASYN_FRAMEFORMATST asyn_frame;
	SYNC_FRAMEFORMATST sync_frame;
	BYTE  PtRxMode;//接收模式
	BYTE  TimeOutThrowFrmEn;//超时丢帧使能
	DWORD timeOutCnt;//超时时间
}ptCGF;

//串口发送配置结构体
typedef struct UartSendCfg
{
	BYTE  SendMode;//发送模式(0:普通,1:定时,2:触发)
	BYTE  SendWord16En;//发送16进制格式使能
	DWORD FrmGap;//帧间隔
	DWORD TrigerCnt;//触发发送次数
}SendCfg;

//串口接收配置结构体
typedef struct UartRecvCfg
{
	DWORD BaudRate; //波特率
	DWORD Parity;   //校验方式
	DWORD DataNum;  //数据位个数
	DWORD StopNum;  //停止位个数
	DWORD IntDeepth;//中断深度
	BYTE  RecvIntEn;//接收中断使能
	BYTE  uartMode;//串口模式(0:rs232,1:rs422,2:rs485)
	BYTE  RecvWord16En;//接收16进制显示使能
	BYTE  SaveRecvDataEn;//保存接收数据使能
	BYTE  ASYN_RecvMode;//协议接收模式(0:FIFO接收,1:刷新接收)
}RecvCfg;

/******************自定义板卡功能接口*******************/
void initApiParam();//初始化api参数操作
void CHR34xxx_OpenCard();//打开板卡操作
void CHR34xxx_send_comm_uartCgf(BYTE ChNum,BYTE ChWorkMode,RecvCfg* m_recvCfg);//异步公共串口配置
void CHR34xxx_recv_comm_uartCgf(BYTE ChNum,BYTE ChWorkMode,RecvCfg* m_recvCfg);//同步公共串口配置
void CHR34xxx_asyn_uartRecvCfg(BYTE ChNum,RecvCfg* m_recvCfg,BYTE ASYN_485SelfCk,BYTE ASYN_RecvMode,ptCGF* m_ptCGF);//异步串口接收配置
void CHR34xxx_sync_uartRecvCfg(BYTE ChNum,RecvCfg* m_recvCfg,ptCGF* m_ptCGF);//同步串口接收配置
void CHR34xxx_asyn_uartSendCfg(BYTE ChNum,SendCfg* m_sendCfg,DWORD ASYN_WordGaP);//异步串口发送配置
void CHR34xxx_sync_uartSendCfg(BYTE ChNum,SendCfg* m_sendCfg,ptCGF* m_ptCGF);//同步串口发送配置
void CHR34xxx_uart_DataSend(BYTE ChNum,SendCfg* m_sendCfg,BYTE ChWorkMode,DWORD dwLen,BYTE* TxBuf);//串口数据发送
void CHR34xxx_CardRecvFuc(BYTE ChNum,bool is_asynPtRecv,bool is_syncMode,bool is_FreshRecv,BYTE* Rxbuf,DWORD* dwResult);//板卡接收相关操作
void CHR34xxx_StartSend(BYTE ChNum,BYTE ChWorkMode,RecvCfg* m_recvCfg,SendCfg* m_sendCfg,ptCGF* m_ptCGF,DWORD ASYN_WordGaP,DWORD dwLen,BYTE* TxBuf);//开始发送响应
void CHR34xxx_StopSend(BYTE ChNum);//停止发送响应
void CHR34xxx_StartRecv(BYTE ChNum,BYTE ChWorkMode,RecvCfg* m_recvCfg,BYTE ASYN_485SelfCk,BYTE ASYN_RecvMode,ptCGF* m_ptCGF);//开始接收响应
void CHR34xxx_StopRecv(BYTE ChNum);//停止接收响应
void CHR34xxx_ResetCard();//复位响应
void CHR34xxx_CloseCard();//关闭响应
void CHR34xxx_RecvData(BYTE ChNum,bool is_IntRecv,bool is_asynPtRecv,bool is_syncMode,bool is_FreshRecv,BYTE* Rxbuf,DWORD* dwResult);//板卡接收数据响应