import logging

from coilsnake.model.eb.music import Chunk


log = logging.getLogger(__name__)


def read_pack(block, offset):
    pack = dict()

    while True:
        chunk = Chunk.create_from_block(block, offset)
        if chunk is None:
            break
        pack[chunk.spc_address] = chunk
        offset += chunk.chunk_size()

    return pack


def get_sequence_pointer(bgm_id, program_chunk):
    return program_chunk.data.read_multi(0x294a + bgm_id*2, 2)


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


def get_sequence_as_chunk(bgm_id, program_chunk, sequence_pack):
    sequence_pointer = get_sequence_pointer(bgm_id=bgm_id, program_chunk=program_chunk)
    log.debug("Reading BGM {:#x}'s sequence from address[{:#x}]".format(bgm_id+1, sequence_pointer))

    # If the sequence is a chunk in the sequence_pack, return the chunk
    if sequence_pack and sequence_pointer in sequence_pack:
        return sequence_pack[sequence_pointer]

    # If the sequence is one of the sequences builtin to the program chunk, return the sequence as a new chunk
    if sequence_pointer in BUILTIN_SEQUENCE_SIZES:
        sequence_size = BUILTIN_SEQUENCE_SIZES[sequence_pointer]
        sequence_offset_in_program = sequence_pointer - program_chunk.spc_address
        return Chunk(sequence_pointer,
                     program_chunk.data[sequence_offset_in_program:sequence_offset_in_program + sequence_size])

    # TODO read in sequences which start in the middle of a sequence chunk
    log.error("Attempted to read invalid sequence @ {:#x}".format(sequence_pointer))
    return None

