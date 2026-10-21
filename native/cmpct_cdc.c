/* CMPCT content-defined chunker prototype.
 *
 * Footnote: chunk boundaries depend on the bytes around each boundary, not absolute file offsets.
 * This means inserting/deleting bytes usually changes only nearby chunks instead of invalidating every
 * later chunk. The container stores each chunk's explicit logical length, so readers do not depend on
 * this algorithm at all; future chunkers can coexist without changing the on-disk read contract.
 */
#include <stdint.h>
#include <stddef.h>

/* Precomputed from the original CMPCTCDC SplitMix64 seed. Keeping the
 * gear table immutable avoids an initialization data race when native
 * calls execute concurrently (ctypes.CDLL releases the Python GIL).
 * Do not change this table to tune CDC; regenerate from the source seed.
 */
static const uint64_t gear[256] = {
    UINT64_C(0x19937d06656a1a0a), UINT64_C(0x8487bba87362e0af), UINT64_C(0xcea7d53d2681908f), UINT64_C(0x9a801da75de8f137),
    UINT64_C(0x05e1db00ff34abff), UINT64_C(0xaff071211f3f743f), UINT64_C(0x2127c02d31eb6247), UINT64_C(0xf03828a7273f8349),
    UINT64_C(0x53b1ef2acbb3b435), UINT64_C(0xabfea7e71ea0d201), UINT64_C(0xfda26e46f350967e), UINT64_C(0x515090633d6d36b7),
    UINT64_C(0x6f15411f7e5ebde0), UINT64_C(0x38a99d5cc4bef7b1), UINT64_C(0xb21f7ed132fea2c3), UINT64_C(0x7e07dcdc7dc9dc11),
    UINT64_C(0xd6e360bbb1fe7682), UINT64_C(0x8e6178398a8266b8), UINT64_C(0x62dab96fdfce9286), UINT64_C(0x92aa9c044c8dc32b),
    UINT64_C(0x9278327cfc8d995d), UINT64_C(0x856f933832d1e81a), UINT64_C(0x8d03cbc5e5a1bc60), UINT64_C(0xed531b4c9a8fc133),
    UINT64_C(0xf45bb4d7e9a8370c), UINT64_C(0x839a3e1d03b386fe), UINT64_C(0xd0476a7bb586b9fe), UINT64_C(0x60047fd15f5dbc78),
    UINT64_C(0xcb487d8c639e3386), UINT64_C(0x2f404207c902bad6), UINT64_C(0x99a8ace9b8020572), UINT64_C(0x1a546939ca02c840),
    UINT64_C(0x547bdbaa4dd22ead), UINT64_C(0x1af20917700bed80), UINT64_C(0x1d0ed95d6ab9deb0), UINT64_C(0xdf3ce1f9a88ca08e),
    UINT64_C(0x0274d96047b3549c), UINT64_C(0xfb0bae443048f57b), UINT64_C(0xea3523ca326ad264), UINT64_C(0x27dd198f85d47620),
    UINT64_C(0x857ee9c9c1e0d66e), UINT64_C(0xd2b90b740bfaae31), UINT64_C(0x617b289acb71f5f2), UINT64_C(0x5761862dfa10748f),
    UINT64_C(0x812f8c5f3f813aa1), UINT64_C(0xfaa93995316b7ff8), UINT64_C(0x7e94582e677f6222), UINT64_C(0x0731c4cb29be8155),
    UINT64_C(0x75dc7f0876755d31), UINT64_C(0x3e5b4f1e59746266), UINT64_C(0xbaf1304821288d93), UINT64_C(0x8e2f696dcc9f703f),
    UINT64_C(0xe76e5f3f297f7f36), UINT64_C(0x1b185359ace221e2), UINT64_C(0x73d2dd8eaaa4a3af), UINT64_C(0x9c5731715f6a94e9),
    UINT64_C(0x2c56232391475a13), UINT64_C(0x548c72b0f443c9bf), UINT64_C(0x060d9c334e450b56), UINT64_C(0x028f8846db50c44e),
    UINT64_C(0x460adaa1d758c94e), UINT64_C(0x43dda7ddcaa15f57), UINT64_C(0x6b29a35a3f5c32b2), UINT64_C(0x0dfa0792790c7ac1),
    UINT64_C(0x85bb2d5c26d55b9e), UINT64_C(0x3b0b58da56ca980f), UINT64_C(0xd028ea4c01edd220), UINT64_C(0xe4a89b0e6862efce),
    UINT64_C(0x3c729221ad95b627), UINT64_C(0x490dc8a8e6372927), UINT64_C(0xc7e3ed1462cb601e), UINT64_C(0x8c2e4ff84bf7e5a0),
    UINT64_C(0x03ab998c7b254759), UINT64_C(0x0b8f1fd20fb5d407), UINT64_C(0xfe3d90317bc683b1), UINT64_C(0x1f88a53dbcf3b647),
    UINT64_C(0x04353f3402d37bac), UINT64_C(0x59114f3305776909), UINT64_C(0xa176a9a0b563465d), UINT64_C(0x20564a96b2919c48),
    UINT64_C(0x1b709e9fa678b76b), UINT64_C(0xc00fa5734814dfae), UINT64_C(0x368f00a509bcbbb1), UINT64_C(0x16259a492c2117a5),
    UINT64_C(0x2cde610db4a2eef9), UINT64_C(0xbc5e2dc1cc99d3b7), UINT64_C(0x6d6086b00770158a), UINT64_C(0x75b51dc8f2f60c27),
    UINT64_C(0xab94898f09807247), UINT64_C(0x556f26f797ea32a7), UINT64_C(0xf6f6fdcedd3ea977), UINT64_C(0x72f262820f474f6a),
    UINT64_C(0x6727ee58698e7fbf), UINT64_C(0x7230def20552ab5c), UINT64_C(0x5b93c1e9ee28f4f5), UINT64_C(0x77b1e3950cde2d7f),
    UINT64_C(0xf40034b61d06d38e), UINT64_C(0x2eae9dc3bcdcb82e), UINT64_C(0x626c6bdb64f233dc), UINT64_C(0xbba5777c81ae5daa),
    UINT64_C(0xfd4e6ed533539b22), UINT64_C(0x6c4a264149745bc1), UINT64_C(0x27e7a70b790ce7eb), UINT64_C(0xd778b5eb72a0f27d),
    UINT64_C(0xea51bcbdff8cb508), UINT64_C(0x54698b048bc25291), UINT64_C(0x107bfea12de48a78), UINT64_C(0x4a1856fe46ac7859),
    UINT64_C(0x2c08a52bbe7fd6d5), UINT64_C(0xd12deae081c37da3), UINT64_C(0x85bd1cbb94740b62), UINT64_C(0x465eac702eff78ac),
    UINT64_C(0xf62fc3de9b44992e), UINT64_C(0x20854d5ee65678e0), UINT64_C(0xd05bad1333c8e668), UINT64_C(0xd18209ea3002c5ac),
    UINT64_C(0xb479b1c20297387d), UINT64_C(0x1b5aa170e79658fb), UINT64_C(0xc34d7e47814664fb), UINT64_C(0xf0fcb17bc3711976),
    UINT64_C(0x2702831ecb9d1002), UINT64_C(0x3024964e45b2b5f8), UINT64_C(0x403dbb72cb525348), UINT64_C(0xacf5a21666b7d3f5),
    UINT64_C(0xe5e1931bf6229cf0), UINT64_C(0x872c52e0c029ad0d), UINT64_C(0x2fd95c1549c0f17a), UINT64_C(0xa183380c4f9081cb),
    UINT64_C(0x6acba3f7592c1ac4), UINT64_C(0xdc36a30eb0851d9e), UINT64_C(0x11c545f609f38990), UINT64_C(0xbda0d1c9e45e4bcf),
    UINT64_C(0x004d62e7ec50357e), UINT64_C(0x62b8a8b08cc8bba6), UINT64_C(0x53219b9d1b46d594), UINT64_C(0x4972e6266843c9e6),
    UINT64_C(0x7bf5c617e5b36d38), UINT64_C(0xe3e835fd0c3bf82a), UINT64_C(0xa230038791c0e7f4), UINT64_C(0x2054ad61430e2a7a),
    UINT64_C(0x864bf5c03a2b60ad), UINT64_C(0x968ce52cbd27bd4f), UINT64_C(0x9ff1cb76840fa1ae), UINT64_C(0xeeacca6257fe9f9c),
    UINT64_C(0x50b99160ef13b48f), UINT64_C(0x479c95633d98c2d1), UINT64_C(0x927661110997a230), UINT64_C(0xb70db34ddc0fd6b1),
    UINT64_C(0x0bc2a8baf92f62e9), UINT64_C(0x7021d5e4df157fda), UINT64_C(0x0096b0ad1b33dcc2), UINT64_C(0x1853ee437044a286),
    UINT64_C(0x8af841a0108e4dd9), UINT64_C(0xa28f59e1760dd3ee), UINT64_C(0x75159991f4fcd701), UINT64_C(0x4c8f0b417eed0fde),
    UINT64_C(0x67a17e3e453fa6fe), UINT64_C(0x9013ba06cdcd12fb), UINT64_C(0xcebb1c0403ab98af), UINT64_C(0x8fb562d0f8cde1d9),
    UINT64_C(0x6b82ea92e908c417), UINT64_C(0x185f52e163591a85), UINT64_C(0x72728f8b996008a6), UINT64_C(0x36ab93a71604b3e8),
    UINT64_C(0xa596175730acd940), UINT64_C(0x332c3af76ca9fec4), UINT64_C(0xa59de91c092c328f), UINT64_C(0x039efd9fa643c5f2),
    UINT64_C(0xc01d133a7dc08555), UINT64_C(0x04761cc44aee6ac2), UINT64_C(0x0822d70702055dc0), UINT64_C(0x9254f8434586b35d),
    UINT64_C(0xaba26e0a007ae191), UINT64_C(0xd7d262dfec28631f), UINT64_C(0x1b927dac9e46d64f), UINT64_C(0x1990428787e850b4),
    UINT64_C(0xafc01f12ba8cde58), UINT64_C(0x92154eb9ce1742c2), UINT64_C(0x8a3541199ee625a9), UINT64_C(0x9ef9cfb7eca40214),
    UINT64_C(0x960ca3bfcc76091b), UINT64_C(0x3be03181920f1354), UINT64_C(0xb5a9c8e8fd432dea), UINT64_C(0x3babedabf9b72b2a),
    UINT64_C(0x9f2802b7f73242f2), UINT64_C(0x1d344aabc25601eb), UINT64_C(0x353b35b974b300e3), UINT64_C(0x93170a5ad4bee3ef),
    UINT64_C(0x5d7e1cec02e77f05), UINT64_C(0x344987d0175a74db), UINT64_C(0x126bfa4e4c3a1c36), UINT64_C(0x80120f0732818479),
    UINT64_C(0x63bb91ec9d7faba0), UINT64_C(0x114026dd87d1efed), UINT64_C(0xe800280bbb21f21a), UINT64_C(0x8a06bc64980a2060),
    UINT64_C(0x0e766cea97026a44), UINT64_C(0x806bf8ad23c56040), UINT64_C(0xeff657ae2a237799), UINT64_C(0xb7f2052880a31cbc),
    UINT64_C(0x21dea495ba834980), UINT64_C(0x6773a3e23cb8f881), UINT64_C(0xc1cd5e89e70cbbad), UINT64_C(0x36e1faf886f38d56),
    UINT64_C(0xbf5ad556eebf300b), UINT64_C(0xed2536c5aa4dc873), UINT64_C(0x4955645b2e835c34), UINT64_C(0x9c5462a427e6b0c1),
    UINT64_C(0xd70845ba261ac8f2), UINT64_C(0x9013e93eb981a0e6), UINT64_C(0xe6cfc8b581110a1d), UINT64_C(0xba6752b236ab1745),
    UINT64_C(0xb084f4fbd78b3736), UINT64_C(0x13fd2309b4dd26e5), UINT64_C(0x213fadf2abecceaf), UINT64_C(0xbb51c17a7d6ed04a),
    UINT64_C(0xa46f3489cfb949ad), UINT64_C(0x5ed17b9af568e03a), UINT64_C(0x2d37d5cb5f7ab543), UINT64_C(0x418ec80087f664b4),
    UINT64_C(0x415522a479d61c06), UINT64_C(0xd372c72b8ca3bf7e), UINT64_C(0x4563bbe6623f7920), UINT64_C(0x141d759b9704023c),
    UINT64_C(0x67a9f26c59c6f4f0), UINT64_C(0x1a78a7fee23b1727), UINT64_C(0x353d5056eb132fbf), UINT64_C(0x4f4321076f694cbb),
    UINT64_C(0x51a0c053beb8ca21), UINT64_C(0x49999e01b6c73dc2), UINT64_C(0x41cddade091c23a5), UINT64_C(0x203e73469dcd5a05),
    UINT64_C(0x85b5f6217f8de8c0), UINT64_C(0x1dccc7f992dd2380), UINT64_C(0xfa37d2d8e8306121), UINT64_C(0x59c0c649454d92b5),
    UINT64_C(0x87b7a5312772ce15), UINT64_C(0x64f13fe521804832), UINT64_C(0x104aac3bb986cc7a), UINT64_C(0xd2a45edc4c10b208),
    UINT64_C(0x93a168c3bfa71fbe), UINT64_C(0x6596a0d80d5432cd), UINT64_C(0xf2e9f75fcc0435bf), UINT64_C(0x6e974029f277c8fa),
    UINT64_C(0x148d84b19bb965f3), UINT64_C(0xe11ed901d9d7a0d6), UINT64_C(0x9fcb533a4c650258), UINT64_C(0xf8590b2a3d8c8f8f),
    UINT64_C(0x4f7e00abcfde7ffb), UINT64_C(0xf738c33f885c9ac6), UINT64_C(0xb8b0ceca06499d74), UINT64_C(0x16ea7318bd0b51b3),
    UINT64_C(0x4e82d29f1806f8ae), UINT64_C(0xcac7f658e191a911), UINT64_C(0xa51f8dd871266db7), UINT64_C(0xfa7ddfcbdc852b66),
};

/* Return number of chunks and write cumulative end offsets to out[].
 * avg must be a power of two. The two-mask normalization keeps chunks away from pathological
 * tiny/huge tails while preserving locality: fewer cuts before avg, more cuts after avg.
 */
size_t cmpct_cdc_cut(const uint8_t *data, size_t n, size_t min_size, size_t avg_size,
                     size_t max_size, uint64_t *out, size_t cap) {
    if (!data || !out || cap == 0 || min_size == 0 || avg_size < min_size || max_size < avg_size)
        return 0;
    if ((avg_size & (avg_size - 1)) != 0) return 0;

    const uint64_t mask_early = (uint64_t)(avg_size * 2 - 1);
    const uint64_t mask_late  = (uint64_t)(avg_size / 2 - 1);
    size_t count = 0, start = 0;
    while (start < n) {
        size_t hard_end = start + max_size;
        if (hard_end > n) hard_end = n;
        size_t i = start + min_size;
        if (i >= hard_end) {
            if (count >= cap) return 0;
            out[count++] = hard_end; start = hard_end; continue;
        }
        size_t normal = start + avg_size;
        if (normal > hard_end) normal = hard_end;
        uint64_t h = 0;
        size_t cut = hard_end;
        for (; i < hard_end; ++i) {
            h = (h << 1) + gear[data[i]];
            uint64_t mask = (i < normal) ? mask_early : mask_late;
            if ((h & mask) == 0) { cut = i + 1; break; }
        }
        if (count >= cap) return 0;
        out[count++] = cut;
        start = cut;
    }
    return count;
}
