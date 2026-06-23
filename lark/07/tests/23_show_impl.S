.section .rodata
.Lstr0:
  .word 3
  .byte 82, 101, 100, 0
.Lstr1:
  .word 5
  .byte 71, 114, 101, 101, 110, 0
.Lstr2:
  .word 4
  .byte 66, 108, 117, 101, 0

.section .text
.globl show$Color
show$Color:
  addi sp, sp, -32
  sw   ra, 28(sp)
  sw   s0, 24(sp)
  addi s0, sp, 32
  sw   s8, -12(s0)
  sw   s9, -16(s0)
  sw   s10, -20(s0)
  sw   s11, -24(s0)
  mv   s11, a0
  mv   t0, s11
  lw   t1, 0(t0)
  mv   s9, t1
  mv   t0, s9
  li   t1, 2  # tag 'Red'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s8, t2
  mv   t0, s8
  bnez t0, .show$Color_arm2
  j    .show$Color_next3
.show$Color_arm2:
  la   t0, .Lstr0
  mv   s10, t0
  j    .show$Color_match_end1
.show$Color_next3:
  mv   t0, s11
  lw   t1, 0(t0)
  mv   s8, t1
  mv   t0, s8
  li   t1, 1  # tag 'Green'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s9, t2
  mv   t0, s9
  bnez t0, .show$Color_arm6
  j    .show$Color_next7
.show$Color_arm6:
  la   t0, .Lstr1
  mv   s10, t0
  j    .show$Color_match_end1
.show$Color_next7:
  mv   t0, s11
  lw   t1, 0(t0)
  mv   s9, t1
  mv   t0, s9
  li   t1, 0  # tag 'Blue'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s8, t2
  mv   t0, s8
  bnez t0, .show$Color_arm10
  j    .show$Color_next11
.show$Color_arm10:
  la   t0, .Lstr2
  mv   s10, t0
  j    .show$Color_match_end1
.show$Color_next11:
  call __lark_match_fail
.show$Color_match_end1:
  mv   a0, s10
  lw   s8, -12(s0)
  lw   s9, -16(s0)
  lw   s10, -20(s0)
  lw   s11, -24(s0)
  lw   ra, 28(sp)
  lw   s0, 24(sp)
  addi sp, sp, 32
  ret

.globl lark_main
lark_main:
  addi sp, sp, -32
  sw   ra, 28(sp)
  sw   s0, 24(sp)
  addi s0, sp, 32
  sw   s8, -12(s0)
  sw   s9, -16(s0)
  sw   s10, -20(s0)
  sw   s11, -24(s0)
  mv   s11, a0
  li   a0, 1
  call __heap_alloc
  mv   t3, a0
  li   t0, 2  # Red
  sw   t0, 0(t3)
  mv   s10, t3
  mv   a0, s10
  call show
  mv   s9, a0
  mv   a0, s11
  mv   a1, s9
  call print
  mv   s10, a0
  li   a0, 1
  call __heap_alloc
  mv   t3, a0
  li   t0, 1  # Green
  sw   t0, 0(t3)
  mv   s9, t3
  mv   a0, s9
  call show
  mv   s8, a0
  mv   a0, s10
  mv   a1, s8
  call print
  mv   s9, a0
  li   a0, 1
  call __heap_alloc
  mv   t3, a0
  li   t0, 0  # Blue
  sw   t0, 0(t3)
  mv   s8, t3
  mv   a0, s8
  call show
  mv   s10, a0
  mv   a0, s9
  mv   a1, s10
  call print
  mv   s8, a0
  li   a0, 42
  call show
  mv   s10, a0
  mv   a0, s8
  mv   a1, s10
  call print
  mv   s9, a0
  li   a0, 1078523331  # float 3.14
  call __show_float
  mv   s10, a0
  mv   a0, s9
  mv   a1, s10
  call print
  mv   s8, a0
  li   a0, 1
  call __show_bool
  mv   s10, a0
  mv   a0, s8
  mv   a1, s10
  call print
  mv   s9, a0
  mv   a0, s9
  lw   s8, -12(s0)
  lw   s9, -16(s0)
  lw   s10, -20(s0)
  lw   s11, -24(s0)
  lw   ra, 28(sp)
  lw   s0, 24(sp)
  addi sp, sp, 32
  ret

