import logging

from coilsnake.exceptions.common.exceptions import OutOfBoundsError

log = logging.getLogger(__name__)

# The sizes of sequences which are embedded inside the "program" chunk. Because these sequences aren't stored as
# individual chunks, their sizes are not stored in the ROM, so the sizes are hardcoded here.
# These values come from BlueStone, who documented these sequences:
#   http://forum.starmen.net/forum/Community/PKHack/Inaccessible-EB-Music-Now-Accessible/page/1
BUILTIN_SEQUENCE_SIZES = {
    0x2FDD: 63,   # 0x04 - None
    0x301C: 478,  # 0x05 - You Win! (Version 1)
    0x31FA: 560,  # 0xB8 - You Win! (Version 3, versus Boss)
    0x342A: 640,  # 0xB7 - Instant Victory
    0x36AA: 220,  # 0x06 - Level Up
    0x3786: 716,  # 0x07 - You Lose
    0x3A52: 303,  # 0x08 - Battle Swirl (Boss)
    0x3B81: 250,  # 0x09 - Battle Swirl (Ambushed)
    0x3C7B: 294,  # 0xB0 - Battle Swirl (Normal)
    0x3DA1: 707,  # 0x0B - Fanfare
    0x4064: 324,  # 0x0C - You Win! (Version 2)
    0x41A8: 240,  # 0x0E - Teleport, Failure
    0x4298: 355,  # 0x0D - Teleport, Departing
    0x43FB: 257,  # 0x87 - Teleport, Arriving
    0x44FC: 97,   # 0x73 - Phone Call
    0x455D: 302,  # 0x7B - New Party Member
}


def read_pack(block, offset):
    pack = dict()

    while True:
        from coilsnake.model.eb.music import Chunk
        chunk = Chunk.create_from_block(block, offset)
        if chunk.data_size() == 0:
            break
        pack[chunk.spc_address] = chunk
        offset += chunk.chunk_size()

    return pack


def write_pack(block, pack):
    pack_size = 2
    for chunk in pack.itervalues():
        pack_size += chunk.chunk_size()

    pack_offset = block.allocate(size=pack_size)

    i = pack_offset
    for chunk in pack.itervalues():
        chunk.write_to_block(block=block, offset=i)
        i += chunk.chunk_size()
    block[i] = 0
    block[i+1] = 0

    return pack_offset


# Returns an offset where a chunk of size "data_size" can be safely inserted into a specified pack without
# - overwriting any other data in the pack
# - conflicting with the space used by other chunks in any "partner packs"
def find_free_offset_in_pack(packs, pack_id, partner_pack_ids, data_size):
    # Find the first range big enough to hold the data
    offset = 0
    pack_ids = {pack_id}.union(partner_pack_ids)
    chunk_starts = {start: pack[start] for i, pack in enumerate(packs) for start in pack if i in pack_ids}
    for start in sorted(chunk_starts):
        if start - offset >= 4 + data_size:
            break
        else:
            offset = start + chunk_starts[start].chunk_size()
    else:
        if offset + 4 + data_size > 0x10000:
            raise OutOfBoundsError(("No free offset could be found in pack {} "
                                   "for data of length[{}]").format(pack_id, data_size))
    return offset


def get_sequence_pointer(bgm_id, program_chunk):
    return program_chunk.data.read_multi(0x2948 + bgm_id*2, 2)


def create_sequence(bgm_id, sequence_pack_id, sequence_pack, program_chunk):
    from coilsnake.model.eb.music import Chunk, Sequence
    sequence_pointer = get_sequence_pointer(bgm_id=bgm_id, program_chunk=program_chunk)
    log.debug("Reading BGM {:#x}'s sequence from address[{:#x}]".format(bgm_id, sequence_pointer))

    # If the sequence is a chunk in the sequence_pack, return the chunk
    if sequence_pack and sequence_pointer in sequence_pack:
        return Sequence.create_from_chunk(chunk=sequence_pack[sequence_pointer],
                                          bgm_id=bgm_id,
                                          sequence_pack_id=sequence_pack_id,
                                          is_always_loaded=False)

    # If the sequence is one of the sequences builtin to the program chunk, return the builtin sequence as a new chunk
    if sequence_pointer in BUILTIN_SEQUENCE_SIZES:
        sequence_size = BUILTIN_SEQUENCE_SIZES[sequence_pointer]
        sequence_offset_in_program = sequence_pointer - program_chunk.spc_address
        chunk = Chunk(spc_address=sequence_pointer,
                      data=program_chunk.data[sequence_offset_in_program:sequence_offset_in_program + sequence_size])
        return Sequence.create_from_chunk(chunk=chunk,
                                          bgm_id=bgm_id,
                                          sequence_pack_id=sequence_pack_id,
                                          is_always_loaded=True)

    # If none of the above are true, create the sequence from the address only
    log.debug("Could not find sequence chunk for bgm_id[{}] @ spc_address[{:#x}], assuming it's a subsequence".format(
        bgm_id, sequence_pointer
    ))
    return Sequence.create_from_spc_address(spc_address=sequence_pointer,
                                            bgm_id=bgm_id,
                                            sequence_pack_id=sequence_pack_id,
                                            is_always_loaded=False)


def remove_sequences_from_program_chunk(program_chunk):
    # 0x2FDD is where the sequence data starts in the program, as shown in BUILTIN_SEQUENCE_SIZES
    program_chunk.truncate(0x2FDD)