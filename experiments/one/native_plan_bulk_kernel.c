#include <stddef.h>
#include <stdint.h>

/* Research kernel for existing ONE xor/add8 operations. No format semantics live here. */

int one_plan_xor_many(uint8_t *out, const uint8_t *const *inputs, size_t input_count, size_t width) {
    if ((width && !out) || input_count < 2 || input_count > 9 || !inputs) return 1;
    for (size_t i = 0; i < width; ++i) out[i] = 0;
    for (size_t k = 0; k < input_count; ++k) {
        const uint8_t *src = inputs[k];
        if (width && !src) return 2;
        for (size_t i = 0; i < width; ++i) out[i] ^= src[i];
    }
    return 0;
}

int one_plan_add8_many(uint8_t *out, const uint8_t *const *inputs, size_t input_count, size_t width) {
    if ((width && !out) || input_count < 2 || input_count > 9 || !inputs) return 1;
    for (size_t i = 0; i < width; ++i) out[i] = 0;
    for (size_t k = 0; k < input_count; ++k) {
        const uint8_t *src = inputs[k];
        if (width && !src) return 2;
        for (size_t i = 0; i < width; ++i) out[i] = (uint8_t)(out[i] + src[i]);
    }
    return 0;
}
