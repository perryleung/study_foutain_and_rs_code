#ifndef _DRIVER_H_
#define _DRIVER_H_

#include <map>
#include "dap.h"
#include "module.h"

#define DRIVER_CONSTRUCT(state)                                                \
    do {                                                                       \
        MODULE_CONSTRUCT(state);                                               \
        GetDap().SetOwner(this);                                               \
    } while (0)

namespace drv {

/*
 * This is the base class of driver,
 * hold an DAP to wait the input data notify
 */
template <typename SelfType, int Layer, int Pid>
class Driver : public mod::Module<SelfType, Layer, Pid>
{
public:
    typedef dap::Dap<SelfType> dap_type;

    inline void Notify() {}
    inline dap_type& GetDap() { return dap_; }
private:
    dap_type dap_;
};

}  // end namespace drv

#endif  // _DRIVER_H_
