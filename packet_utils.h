

#ifndef PACKET_UTILS_H_
#define PACKET_UTILS_H_

// Create a bit mask of the given size
#define MASK_BITS(size) ((1 << size) - 1)
// Get size bits from byte at offset
#define GET_BITS(pkt, index, offset, size) (pkt[index] >> offset & MASK_BITS(size))
// Set size bits in byte at offset
#define SET_BITS(pkt, index, offset, size, val) (pkt[index] = (pkt[index] & ~MASK_BITS(size)) | ((val & MASK_BITS(size)) << offset))
// Set byte in packet
#define GET_UINT8(pkt, index) ((pkt)[(index)])
// Get byte in packet
#define SET_UINT8(pkt, index, val) (pkt)[(index)] = (val)
// Get 2byte in packet
#define GET_UINT16(pkt, index) ( \
    (uint16_t)(pkt)[(index)] | ((uint16_t)(pkt)[(index) + 1] << 8) \
)
// Set 2byte in packet
#define SET_UINT16(pkt, index, val) do {          \
    (pkt)[(index)] = (uint8_t)((val) & 0xFF);     \
    (pkt)[(index) + 1] = (uint8_t)(((val) >> 8) & 0xFF); \
} while (0)
// Get 4 byte in packet
#define GET_UINT32(pkt, index) ( \
    (uint32_t)(pkt)[(index)] | ((uint32_t)(pkt)[(index) + 1] << 8) | \
    ((uint32_t)(pkt)[(index) + 2] << 16) | ((uint32_t)(pkt)[(index) + 3] << 24) \
)
// Set 4 byte in packet
#define SET_UINT32(pkt, index, val) do {          \
    (pkt)[(index)] = (uint8_t)((val) & 0xFF);     \
    (pkt)[(index) + 1] = (uint8_t)(((val) >> 8) & 0xFF);  \
    (pkt)[(index) + 2] = (uint8_t)(((val) >> 16) & 0xFF); \
    (pkt)[(index) + 3] = (uint8_t)(((val) >> 24) & 0xFF); \
} while (0)
// Get 8 byte in packet
#define GET_UINT64(pkt, index) ( \
    (uint64_t)(pkt)[(index)] | ((uint64_t)(pkt)[(index) + 1] << 8) | \
    ((uint64_t)(pkt)[(index) + 2] << 16) | ((uint64_t)(pkt)[(index) + 3] << 24) | \
    ((uint64_t)(pkt)[(index) + 4] << 32) | ((uint64_t)(pkt)[(index) + 5] << 40) | \
    ((uint64_t)(pkt)[(index) + 6] << 48) | ((uint64_t)(pkt)[(index) + 7] << 56) \
)
// Set 8 byte in packet
#define SET_UINT64(pkt, index, val) do {          \
    (pkt)[(index)] = (uint8_t)((val) & 0xFF);     \
    (pkt)[(index) + 1] = (uint8_t)(((val) >> 8) & 0xFF);  \
    (pkt)[(index) + 2] = (uint8_t)(((val) >> 16) & 0xFF); \
    (pkt)[(index) + 3] = (uint8_t)(((val) >> 24) & 0xFF); \
    (pkt)[(index) + 4] = (uint8_t)(((val) >> 32) & 0xFF); \
    (pkt)[(index) + 5] = (uint8_t)(((val) >> 40) & 0xFF); \
    (pkt)[(index) + 6] = (uint8_t)(((val) >> 48) & 0xFF); \
    (pkt)[(index) + 7] = (uint8_t)(((val) >> 56) & 0xFF); \
} while (0)

#endif // PACKET_UTILS_H_
