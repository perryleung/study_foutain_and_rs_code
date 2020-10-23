#ifndef _UTILS_H_
#define _UTILS_H_

#include <memory>
#include <queue>

#define ELPP_DISABLE_TRACE_LOGS
#define ELPP_DISABLE_DEFAULT_CRASH_HANDLING
#define ELPP_STL_LOGGING
#include "easylogging++.h"

#include "message.h"
#include "singleton.h"
#include "config.h"

template <typename T>
using Ptr = std::shared_ptr<T>;

struct IOData
{
    int fd;
    char* data;
    size_t len;
};

typedef Ptr<IOData> IODataPtr;

template <typename SelfType, typename DataType>
class QueueBase : public utils::Singleton<SelfType>
{
public:
    typedef SelfType class_type;
    typedef DataType data_type;
    typedef std::queue<data_type> queue_type;

    static inline data_type& Front() { return GetQueue().front(); }
    static inline data_type& Back() { return GetQueue().back(); }
    static inline bool Empty() { return GetQueue().empty(); }
    static inline size_t Size() { return GetQueue().size(); }
    static inline void Push(const data_type& v)
    {
        LOG(TRACE) << "Push data to Queue";
        return GetQueue().push(v);
    }

    static inline void Pop()
    {
        LOG(TRACE) << "Pop data from Queue";
        return GetQueue().pop();
    }

private:
    static inline queue_type& GetQueue()
    {
        return class_type::Instance().queue_;
    }

private:
    queue_type queue_;
};

class ReadQueue : public QueueBase<ReadQueue, IODataPtr>
{
};
class WriteQueue : public QueueBase<WriteQueue, IODataPtr>
{
};
class UIWriteQueue : public QueueBase<UIWriteQueue, IODataPtr>
{
};
class TraceWriteQueue : public QueueBase<TraceWriteQueue, IODataPtr>
{
};
class ReqQueue : public QueueBase<ReqQueue, msg::MsgReqPtr>
{
};
class RspQueue : public QueueBase<RspQueue, msg::MsgRspPtr>
{
};
class NtfQueue : public QueueBase<NtfQueue, msg::MsgNtfPtr>
{
};



#endif  // _UTILS_H_
