#ifndef TFTP_SERVER__H
#define TFTP_SERVER__H


#define MAX_ERR_MESSAGE_LEN 256
#define MAX_FILENAME_LEN 100
#define TFTP_MODE "octet"

#define RRQ   (1) // [Opcode (2 bytes)] [Filename (string)] [0x00] [Mode (string "octet")] [0x00]
#define WRQ   (2) // [Opcode (2 bytes)] [Filename (string)] [0x00] [Mode (string "octet")] [0x00]
#define DATA  (3) // [Opcode (2 bytes)] [Block # (2 bytes)] [Data (0-512 bytes)]
#define ACK   (4) // [Opcode (2 bytes)] [Block # (2 bytes)]
#define ERROR (5) // [Opcode (2 bytes)] [Error Code (2 bytes)] [Error Msg (string)] [0x00]



#endif
