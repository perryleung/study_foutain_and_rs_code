#include <netdb.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/types.h>


#include "clientsocket.h"


// bool ClientSocket::is_connected_ = false;
ClientSocketMap ClientSocket::clientsocketmap_;

void
ClientSocket::ReadCB(EV_P_ ev_io *w, int revents)
{
    IODataPtr data(new IOData);
    char *p = (char *)malloc(sizeof(char) * BUFFER_SIZE);
    if (!p) {                   // �ڴ����ʧ��
        return;
    }
    memset((void*)p, 0, BUFFER_SIZE);


    ssize_t count = LibevTool::Instance().Readn(w->fd, p, BUFFER_SIZE);

    if (count == 0) {           // û���κ�����

        free(p);                // �ͷŵ�ַ
        close(w->fd);           // �ر�TCP����  �����Ҫ�ر������� ��Ҫ
        ev_io_stop(EV_A_ w);          // ֹͣ�¼�     �����Ҫ�����¼��� ��Ҫ
        LOG(DEBUG) << "socket close, stop the connection between computer and point";
        clientsocketmap_.Delete(w->fd);
        return;
    }else if(count == -1)       // ����
        {
            free(p);            // �Լ����ϵģ�����Ӧ���ͷŵ�ַ
            close(w->fd);       // �Լ����ϵ�
            ev_io_stop(EV_A_ w);       // �Լ����ϵ�
            LOG(DEBUG) << "socket error, stop the connection between computer and point";
            clientsocketmap_.Delete(w->fd);
            // is_connected_ = false;
            return;          // Ϊɶ��������ͷŵ�ַ�ر����ӣ�
        }


 //   p[count] = '\0';

    data->fd   = w->fd;
    data->data = p;
    data->len  = count;

    LOG(DEBUG) << "Read " << data->len << " bytes data from fd " << data->fd;

    ReadQueue::Push(data);      // �������ϵݽ���

    return;
}

ClientSocketPtr
ClientSocket::NewClient(string hostname, string port)
{
    pair<string, string> sock = make_pair(hostname, port);
    ClientSocketPtr targetClient =  clientsocketmap_.Find(sock);

    if (targetClient == NULL) {
        targetClient = make_shared<ClientSocket>();
        if (targetClient->Init(hostname, port)) {
            clientsocketmap_.Insert(sock, targetClient->fd_, targetClient); // ������һ
        }
    }

    return targetClient;        // ��Ȼ����ֵ��һ������ָ�룬���Ƿ��صĶ���ֵ��һ�������룬���Բ��������Ӽ����ģ�������漴ʹ��make_shared�ˣ����Ǵ����׽���ʧ�ܵĻ���������ָ��������ǻ�Ϊ0
}


bool
ClientSocket::Init(string hostname, string port)
{
    server_addr_ = hostname;
    server_port_ = port;

    struct addrinfo hints;      // UNIX�����̾�һ���³���U1����246ҳ,��Ҫ���صĵ�ַ��һЩ������Ϣ
    struct addrinfo *res, *p;   // res��getaddrinfo�Ĳ�ѯ�����p����ǳ����
    int m_sock = 0;

    fd_ = -1;

    memset(&hints, 0, sizeof(struct addrinfo)); // �Ƚ�hints���,hints = 0

    hints.ai_family   = AF_INET; // IPv4
    hints.ai_socktype = SOCK_STREAM; // TCP
    hints.ai_flags    = AI_CANONNAME; // ���������Ĺ淶����
    hints.ai_protocol = 0; /* Any protocol */

    if (getaddrinfo(server_addr_.c_str(), server_port_.c_str(), &hints, &res) != 0) { //U1 P246 ����hostname��port���Լ��������ص���Ϣ�ڽṹ��hints�У����ذ������з���Ҫ��ĵ�ַ�����������ʽ��
        return false;
    }

    for (p = res; p != NULL; p = p->ai_next) { // ���Բ���U1 P255
        m_sock = socket(p->ai_family, p->ai_socktype, p->ai_protocol);
        if (m_sock == -1) {
            continue;
        }
        if (connect(m_sock, p->ai_addr, p->ai_addrlen) != -1) { // �ͻ������ӣ�ֻҪ���ӵ�һ�������˳�
            break;
        }
        close(m_sock);          // ���ܳɹ�connect�Ļ�����Ҫclose��
    }

    if (p == NULL) {
        return false;
    }
        // is_connected_ = true;
    freeaddrinfo(res);          // U1 P251

    LibevTool::Instance().Setnonblock(m_sock);        // ���÷����� U1 P343
    fd_ = m_sock;
    ev_io_init(&read_io_, ReadCB, fd_, EV_READ);
    ev_io_start(LibevTool::Instance().GetLoop(), &read_io_);
    ev_io_init(&write_io_, LibevTool::WritefdCB<WriteQueue>, fd_, EV_WRITE);

    return true;
}

bool ClientSocket::Free()
{
    if (close(fd_) == -1) {
        return false;
    }
    return true;
}

void ClientSocket::Write()
{
    // ev_io_init(&write_io_, WriteCB, fd_, EV_WRITE);
    ev_io_start(LibevTool::Instance().GetLoop(), &write_io_);
}

int ClientSocket::GetFd() { return fd_; }

