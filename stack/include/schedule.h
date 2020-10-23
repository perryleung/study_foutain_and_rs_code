#ifndef _SCHEDULE_H_
#define _SCHEDULE_H_

#include <cstdlib>
#include "dap.h"
#include "message.h"
#include "sap.h"
#include "utils.h"
#include "trace.h"
#include <ev.h>

using std::cout;
using std::endl;

namespace sched {

class Scheduler
{
public:
    static Scheduler& Instance()
    {
        static Scheduler the_instance;
        return the_instance;
    }

    static void Sched(EV_P_ ev_prepare *w, int revents)
    {
        while (!ReadQueue::Empty() || !ReqQueue::Empty() || !RspQueue::Empty() ||
            !NtfQueue::Empty()) 
	    {
		    if (!ReadQueue::Empty()) {
                SchedRead();
            } else if (!RspQueue::Empty()) {
                SchedRsp();
		    } else if (!ReqQueue::Empty()) {
                SchedReq();
		    } else if (!NtfQueue::Empty()) {
                SchedNtf();
		    }
        }
        //Sched();
    }

private:
    static void SchedRead()
    {
        IODataPtr d = ReadQueue::Front();

        dap::DapBase* p = dap::DapMap::Find(d->fd);

        LOG(TRACE) << "receive Data from FD: " << d->fd;

        p->Notify();
    }

    static void SchedReq()
    {
        msg::MsgReqPtr d = ReqQueue::Front();

        sap::SapBase* p = sap::SapMap::Find(d->DstLayer, d->DstPid);

        LOG(DEBUG) << "Layer: " << d->DstLayer << " Pid: " << d->DstPid
                   << " receive Request from Layer: " << d->SrcLayer
                   << " Pid: " << d->SrcPid;

        p->RecvReq(d->msg, d->SrcLayer, d->SrcPid);

        ReqQueue::Pop();
    }

    static void SchedRsp()
    {
        msg::MsgRspPtr d = RspQueue::Front();

        sap::SapBase* p = sap::SapMap::Find(d->DstLayer, d->DstPid);

        LOG(DEBUG) << "Layer: " << d->DstLayer << " Pid: " << d->DstPid
                   << " receive Response from Layer: " << d->SrcLayer
                   << " Pid: " << d->SrcPid;

        p->RecvRsp(d->msg);

        RspQueue::Pop();
    }

    static void SchedNtf()
    {
        msg::MsgNtfPtr d = NtfQueue::Front();

        sap::SapBase* p = sap::SapMap::Find(d->DstLayer, d->DstPid);

        LOG(DEBUG) << "Layer: " << d->DstLayer << " Pid: " << d->DstPid
                   << " receive Notification from Layer: " << d->SrcLayer
                   << " Pid: " << d->SrcPid;

        p->RecvNtf(d->msg);

        NtfQueue::Pop();
    }

    Scheduler() {}
    ~Scheduler() {}
};
}

#endif  // _SCHEDULE_H_
