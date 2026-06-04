#pragma once
#include <stdint.h>
#include <stddef.h>

int op_g(const char *anchor, const char *stamp, uint32_t slot, const char *answer, uint16_t stored);
uint32_t op_m(const uint32_t *values, size_t count);
