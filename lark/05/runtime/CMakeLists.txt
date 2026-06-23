cmake_minimum_required(VERSION 3.13)

set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# ── Pico SDK bootstrap (mirrors the VS Code extension pattern) ────────────────
if(WIN32)
    set(USERHOME $ENV{USERPROFILE})
else()
    set(USERHOME $ENV{HOME})
endif()
set(sdkVersion        2.2.0)
set(toolchainVersion  RISCV_ZCB_RPI_2_2_0_3)
set(picotoolVersion   2.2.0-a4)
set(picoVscode ${USERHOME}/.pico-sdk/cmake/pico-vscode.cmake)
if(EXISTS ${picoVscode})
    include(${picoVscode})
endif()

set(PICO_BOARD pico2 CACHE STRING "Board type")

include(${USERHOME}/.pico-sdk/sdk/${sdkVersion}/external/pico_sdk_import.cmake)

project(lark_pico C CXX ASM)

pico_sdk_init()

# ── The compiled Lark program ─────────────────────────────────────────────────
set(LARK_ASM "${CMAKE_CURRENT_SOURCE_DIR}/program.S"
    CACHE FILEPATH "Lark-generated assembly file")

if(NOT EXISTS "${LARK_ASM}")
    message(WARNING "LARK_ASM not found: ${LARK_ASM}")
endif()

# ── Executable ───────────────────────────────────────────────────────────────
add_executable(lark_pico
    lark_entry.c
    runtime.c
    platform_pico.c
    "${LARK_ASM}"
)

target_compile_definitions(lark_pico PRIVATE PICO_BUILD=1)
target_include_directories(lark_pico PRIVATE "${CMAKE_CURRENT_SOURCE_DIR}")

target_link_libraries(lark_pico
    pico_stdlib
    pico_float
    m
)

pico_enable_stdio_usb(lark_pico  1)
pico_enable_stdio_uart(lark_pico 0)

pico_add_extra_outputs(lark_pico)
