using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using System.Linq;
using System.Threading;
using System.Text;
using System.IO;
using System.Threading.Tasks;

namespace CHR34XXX_ASYN
{
    class Program
    {
        //导入ms库
        [DllImport("msvcrt.dll")]
        //声明函数kbhit
        public static extern int _kbhit();
        static void Main(string[] args)
        {
            int maxChNum = 8;//最大通道数
            int devId = 0;//板卡号
            IntPtr hEvt = new IntPtr();//中断句柄
            CHR_DEVPARST stDevParInfo = new CHR_DEVPARST();//板卡信息结构体
            CHR_DEVBUSST stDevBusInfo = new CHR_DEVBUSST();//板卡总线信息结构体
            
            Byte ChNum = 1;//测试通道
            CHRUART_DCB_ST stRsdcb = new CHRUART_DCB_ST();//串口数据传输格式配置结构体
            stRsdcb.BaudRate = 115200;//波特率
            stRsdcb.ByteSize = 8;//数据位
            stRsdcb.StopBits = 0;//停止位
            stRsdcb.Parity = 0;//校验位
            

            Byte RecvIntEn = 0;//配置中断接收(0:禁止中断,1:使能中断)
            Byte ChWorkMode = 1;//设置工作类型(0:同步模式,1:异步模式)
            Byte uartMode = 1;//设置串口工作模式(0:rs232,1:rs422,2:rs485)
            Byte ASYN_485SelfCk = 0;//设置是否开启485自检(0:禁止,1:486自检使能)
            Byte ASYN_RecvMode = 1;//设置异步接收模式(0:透明模式，1:协议模式)
            Byte PtRxMode = 0;//协议接收模式(0:FIFO接收,1:刷新接收)
            UInt32 IntDeepth = 3;//中断深度
            Byte TimeOutThrowFrmEn = 0;//超时丢帧使能(0:禁止,1:使能)
            UInt32 timeOutCnt = 0;//超时丢帧时间
            Byte SendMode = 0;//发送模式(0:普通,1:定时)
            UInt32 ASYN_WordGaP = 8;//发送字间隔
            UInt32 FrmGap = 100000;//定时发送周期us


            CHRUART_ASYN_PROTOCOL_ST stFrame = new CHRUART_ASYN_PROTOCOL_ST();//异步协议接收配置结构体
            stFrame.CheckSum = 0;//校验和使能(0:禁止,1:使能)
            stFrame.CheckHead = 0;//值为1时，表示校验和包含帧起始符，值为0时，表示校验和不包含帧起始符
            stFrame.ProtocolNo = 0;//协议号(0~12)
            stFrame.SFH = 0xa1;
            stFrame.EFH = 0xa2;
            stFrame.STOF = 0xb1;
            stFrame.ETOF = 0xb2;
            stFrame.PtlLen = 0;//帧长度

            
            //打开板卡
            if (CHR34XXXAPI.CHR34XXX_OpenDev(devId)==0)
            {
                Console.Write("Err:CHR34XXX_OpenDev-error!\n");
                Console.ReadKey();
                return;
            }
            //获取板卡信息
            if (CHR34XXXAPI.CHR34XXX_GetDevParInfo(devId,ref stDevParInfo) == 0)
            {
                Console.Write("Err:CHR34XXX_GetDevParInfo-error!\n");
                Console.ReadKey();
                return;
            }
            //获取设备总线信息
            if (CHR34XXXAPI.CHR34XXX_GetDevBusInfo(devId,ref stDevBusInfo) == 0)
            {
                Console.Write("Err:CHR34XXX_GetDevBusInfo-error!\n");
                Console.ReadKey();
                return;
            }
            //打印SN号
            Console.Write("SN=0x");
            Console.WriteLine(stDevParInfo.dwSN.ToString("X"));

            ////复位板卡
            //if (CHR34XXXAPI.CHR34XXX_ResetDev(devId)==0)
            //{
            //    Console.Write("Err:CHR34XXX_ResetDev-error!\n");
            //    Console.ReadKey();
            //    return;
            //}

            //初始化发送buf
            UInt32 dwLen = 10;//发送长度
            Byte[] TxBuf = new Byte[256];//发送buf
            dwLen = 7;//发送长度
            TxBuf[0] = 0xa1;
            TxBuf[1] = 0xa2;
            TxBuf[2] = 0x03;
            TxBuf[3] = 0x11;
            TxBuf[4] = 0x22;
            TxBuf[5] = 0x33;
            TxBuf[6] = 0x00;
            // //////////////板卡接收配置///////////////
	        //设置工作类型
	        if(ChNum%2 == 0)//奇数通道设置
	        {
		        if(CHR34XXXAPI.CHR34XXX_Ch_SetType(devId,(Byte)(ChNum+1),ChWorkMode)==0)
		        {
                    Console.Write("Err:CHR34XXX_Ch_SetType-error!\n");
                    Console.ReadKey();
                    return;
		        }
	        }
	        else
	        {
		        if(CHR34XXXAPI.CHR34XXX_Ch_SetType(devId,ChNum,ChWorkMode)==0)
		        {
                    Console.Write("Err:CHR34XXX_Ch_SetType-error!\n");
                    Console.ReadKey();
                    return;
		        }
	        }
	        //设置串口数据传输格式
	        if(CHR34XXXAPI.CHR34XXX_Ch_SetCommState(devId,ChNum,ref stRsdcb)==0)
	        {
                Console.Write("Err:CHR34XXX_Ch_SetType-error!\n");
                Console.ReadKey();
                return;
	        }

            //设置串口工作模式
            if (CHR34XXXAPI.CHR34XXX_Ch_SetMode(devId, ChNum,uartMode) == 0)
            {
                Console.Write("Err:CHR34XXX_Ch_SetMode-error!\n");
                Console.ReadKey();
                return;
            }
            // ////////////////配置接收////////////////
            //设置是否开启485自检
            if (CHR34XXXAPI.CHR34XXX_Asyn_Ch_RS485LoopBack(devId, ChNum, ASYN_485SelfCk) == 0)//开启485自检
            {
                Console.Write("Err:CHR34XXX_Asyn_Ch_RS485LoopBack-error!\n");
                Console.ReadKey();
                return;
            }
            //设置异步接收模式(0:透明模式，1:协议模式)
            if (CHR34XXXAPI.CHR34XXX_Asyn_RxCh_SetMode(devId, ChNum,ASYN_RecvMode) == 0)
            {
                Console.Write("Err:CHR34XXX_Asyn_RxCh_SetMode-error!\n");
                Console.ReadKey();
                return;
            }
            //设置接收FIFO模式
            if (CHR34XXXAPI.CHR34XXX_FM_Ch_RxMode(devId, ChNum,PtRxMode) == 0)
            {
                Console.Write("Err:CHR34XXX_FM_Ch_RxMode-error!\n");
                Console.ReadKey();
                return;
            }
            //异步协议接收设置
            if (CHR34XXXAPI.CHR34XXX_Asyn_RxCh_SetProtocol(devId, ChNum, ref stFrame) == 0)
            {
                Console.Write("Err:CHR34XXX_Asyn_RxCh_SetProtocol-error!\n");
                Console.ReadKey();
                return;
            }
            //超时丢帧使能
            if (CHR34XXXAPI.CHR34XXX_FM_Ch_TimeOutEn(devId, ChNum, TimeOutThrowFrmEn) == 0)
            {
                Console.Write("Err:CHR34XXX_FM_Ch_TimeOutEn-error!\n");
                Console.ReadKey();
                return;
            }
            //设置超时丢帧时间
            if (CHR34XXXAPI.CHR34XXX_FM_Ch_SetTimeOut(devId, ChNum, timeOutCnt) == 0)
            {
                Console.Write("Err:CHR34XXX_FM_Ch_SetTimeOut-error!\n");
                Console.ReadKey();
                return;
            }
            //超时丢帧数据量清零
            if (CHR34XXXAPI.CHR34XXX_FM_Ch_ClearTimeOut(devId, ChNum) == 0)
            {
                Console.Write("Err:CHR34XXX_FM_Ch_ClearTimeOut-error!\n");
                Console.ReadKey();
                return;
            }

            /****************异步发送配置********************/
            //设置串口数据发送模式
            if (CHR34XXXAPI.CHR34XXX_TxCh_SetMode(devId, ChNum, SendMode) == 0)
            {
                Console.Write("Err:CHR34XXX_TxCh_SetMode-error!\n");
                Console.ReadKey();
                return;
            }
            //设置发送字间隔
            if (CHR34XXXAPI.CHR34XXX_Asyn_TxCh_SetWordGap(devId, ChNum, ASYN_WordGaP)==0)
            {
                Console.Write("Err:CHR34XXX_Asyn_TxCh_SetWordGap-error!\n");
                Console.ReadKey();
                return;
            }


            //设置定时发送周期
            if (CHR34XXXAPI.CHR34XXX_TxCh_SetPeriod(devId, ChNum, FrmGap) == 0)
            {
                Console.Write("Err:CHR34XXX_TxCh_SetPeriod-error!\n");
                Console.ReadKey();
                return;
            }
            // ////////////////定时发送数据////////////////
            //停止定时发送
            CHR34XXXAPI.CHR34XXX_TxCh_Stop(devId, ChNum);
            UInt32 FIFOCounttmp = 0;
            if (CHR34XXXAPI.CHR34XXX_TxCh_FIFOCount(devId, ChNum, ref FIFOCounttmp) == 0)
            {
                Console.Write("Err:CHR34XXX_TxCh_FIFOCount-error!\n");
                Console.ReadKey();
                return;
            }
            if (FIFOCounttmp == 0)
            {
                UInt32 dwResult = 0;
                if (CHR34XXXAPI.CHR34XXX_TxCh_Write(devId, ChNum, dwLen, TxBuf, ref dwResult) == 0)
                {
                    Console.Write("Err:CHR34XXX_TxCh_Write-error!\n");
                    Console.ReadKey();
                    return;
                }
            }
            //开始定时发送
            CHR34XXXAPI.CHR34XXX_TxCh_Start(devId, ChNum);

            while (_kbhit() == 0)
            {
            }

            //关闭板卡
            if (hEvt != null)
                CHR34XXXAPI.CHR34XXX_RxInt_CloseEvent(devId, hEvt);
            if (CHR34XXXAPI.CHR34XXX_ResetDev(devId)==0)
            {
                Console.Write("Err:CHR34XXX_ResetDev-error!\n");
                Console.ReadKey();
                return;
            }
            if (CHR34XXXAPI.CHR34XXX_CloseDev(devId)==0)
            {
                Console.Write("Err:CHR34XXX_CloseDev-error!\n");
                Console.ReadKey();
                return;
            }
        }
    }
}
