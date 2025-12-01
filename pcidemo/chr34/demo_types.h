// demo_types.h
#pragma once
#include <cstdint>

using BYTE  = unsigned char;
using DWORD = unsigned long;
using bool8 = unsigned char; // 如果你想让大小与 DLL 对齐

struct RecvCfg {
    DWORD BaudRate = 115200;
    BYTE  Parity   = 0;   // 0无 1奇 2偶
    BYTE  StopNum  = 0;   // 0:1 1:1.5 2:2
    BYTE  DataNum  = 8;   // 5..8
    BYTE  ASYN_RecvMode = 0; // 0透明 1协议
    BYTE  IntDeepth = 5;      // 中断深度(1..16) 这里示例用 5
    BYTE  RecvIntEn = 0;      // 0禁用 1使能
    BYTE  uartMode  = 2;      // 0:232 1:422 2:485
    BYTE  RecvWord16En = 1;   // 16 进制显示
};

struct SendCfg {
    BYTE  SendMode = 0;       // 0普通 1定时
    BYTE  SendWord16En = 1;   // 16 进制
    DWORD FrmGap = 100000;    // us，定时周期
};

struct ASYN_FRAME {
    BYTE  HDR   = 0xA1;
    BYTE  EDR   = 0xA2;
    BYTE  TailA = 0xB1;
    BYTE  TailB = 0xB2;
    BYTE  LENR  = 3;
    BYTE  pt_num = 0;
    BYTE  SumCheckEN = 0;
    BYTE  HeadIncluded = 0;
};

struct SYNC_FRAME {
    BYTE HR[4] = {0xA1,0xA2,0xA3,0xA4};
    BYTE ER[4] = {0xB1,0xB2,0xB3,0xB4};
    BYTE FrameIDCnt = 4;
    BYTE FrameIDOrder = 0;      // 0先高后低
    BYTE FrameIDLocation = 3;
    BYTE LocationAddress = 0;
    BYTE SYNCWordCnt = 4;
    BYTE CRCInitVal = 1;
    BYTE CRCOrder = 0;          // 0低位在前
    BYTE ErrFrameEn = 0;
    BYTE SendEdge = 0;          // 0下降沿
    BYTE RecvEdge = 1;          // 1上升沿
    BYTE RecvMode = 0;          // 0普通 1监听
    BYTE AddressTesting = 0;
    BYTE CRCTesting = 0;
    BYTE SYNCWordTesting = 0;
    BYTE CodeErrTesting = 0;
    BYTE lackCntTesting = 0;
};

struct ptCGF {
    ASYN_FRAME asyn_frame;
    SYNC_FRAME sync_frame;
    BYTE  PtRxMode = 1;           // 0 FIFO 1刷新
    BYTE  TimeOutThrowFrmEn = 0;  // 超时丢帧
    DWORD timeOutCnt = 0;         // 超时计数
};

