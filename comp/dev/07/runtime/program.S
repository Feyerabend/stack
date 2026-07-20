.section .rodata
  .p2align 2
.Lstr0:
  .word 12
  .byte 101, 120, 112, 101, 99, 116, 101, 100, 32, 39, 41, 39, 0
  .p2align 2
.Lstr1:
  .word 22
  .byte 101, 120, 112, 101, 99, 116, 101, 100, 32, 110, 117, 109, 98, 101, 114, 32, 111, 114, 32, 39, 40, 39, 0
  .p2align 2
.Lstr2:
  .word 1
  .byte 40, 0
  .p2align 2
.Lstr3:
  .word 1
  .byte 43, 0
  .p2align 2
.Lstr4:
  .word 1
  .byte 41, 0
  .p2align 2
.Lstr5:
  .word 1
  .byte 45, 0
  .p2align 2
.Lstr6:
  .word 1
  .byte 42, 0
  .p2align 2
.Lstr7:
  .word 1
  .byte 47, 0
  .p2align 2
.Lstr8:
  .word 0
  .byte 0
  .p2align 2
.Lstr9:
  .word 1
  .byte 32, 0
  .p2align 2
.Lstr10:
  .word 13
  .byte 32, 32, 61, 62, 32, 32, 69, 82, 82, 79, 82, 58, 32, 0
  .p2align 2
.Lstr11:
  .word 6
  .byte 32, 32, 61, 62, 32, 32, 0
  .p2align 2
.Lstr12:
  .word 5
  .byte 32, 32, 61, 32, 32, 0

.section .text
.globl pand$lam0
pand$lam0:
  addi sp, sp, -48
  sw   ra, 44(sp)
  sw   s0, 40(sp)
  addi s0, sp, 48
  sw   s5, -12(s0)
  sw   s6, -16(s0)
  sw   s7, -20(s0)
  sw   s8, -24(s0)
  sw   s9, -28(s0)
  sw   s10, -32(s0)
  sw   s11, -36(s0)
  mv   s11, a0
  mv   s10, a1
  mv   t0, s11
  lw   t1, 4(t0)
  mv   s8, t1
  mv   t0, s11
  lw   t1, 8(t0)
  mv   s6, t1
  mv   t0, s6
  lw   t1, 0(t0)
  mv   a0, t0
  mv   a1, s10
  jalr ra, 0(t1)
  mv   s7, a0
  mv   t0, s7
  lw   t1, 0(t0)
  mv   s6, t1
  mv   t0, s6
  li   t1, 3  # tag 'Err'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s5, t2
  mv   t0, s5
  bnez t0, .pand$lam0_tag_ok9
  j    .pand$lam0_next6
.pand$lam0_tag_ok9:
  mv   t0, s7
  lw   t1, 4(t0)
  mv   s5, t1
  j    .pand$lam0_sub11
.pand$lam0_sub11:
  j    .pand$lam0_arm5
.pand$lam0_arm5:
  mv   t0, s7
  lw   t1, 4(t0)
  mv   s5, t1
  li   a0, 2
  call __heap_alloc
  mv   t3, a0
  li   t0, 3  # Err
  sw   t0, 0(t3)
  mv   t0, s5
  sw   t0, 4(t3)
  mv   s10, t3
  mv   t0, s10
  mv   s9, t0
  j    .pand$lam0_match_end4
.pand$lam0_next6:
  mv   t0, s7
  lw   t1, 0(t0)
  mv   s10, t1
  mv   t0, s10
  li   t1, 7  # tag 'Ok'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s5, t2
  mv   t0, s5
  bnez t0, .pand$lam0_tag_ok18
  j    .pand$lam0_next15
.pand$lam0_tag_ok18:
  mv   t0, s7
  lw   t1, 4(t0)
  mv   s5, t1
  mv   t0, s5
  lw   t1, 4(t0)
  mv   s10, t1
  j    .pand$lam0_sub22
.pand$lam0_sub22:
  mv   t0, s5
  lw   t1, 8(t0)
  mv   s10, t1
  j    .pand$lam0_sub24
.pand$lam0_sub24:
  j    .pand$lam0_sub20
.pand$lam0_sub20:
  j    .pand$lam0_arm14
.pand$lam0_arm14:
  mv   t0, s7
  lw   t1, 4(t0)
  mv   s5, t1
  mv   t0, s5
  lw   t1, 4(t0)
  mv   s10, t1
  mv   t0, s5
  lw   t1, 8(t0)
  mv   s11, t1
  mv   t0, s8
  lw   t1, 0(t0)
  mv   a0, t0
  mv   a1, s10
  jalr ra, 0(t1)
  mv   s5, a0
  mv   t0, s5
  lw   t1, 0(t0)
  mv   a0, t0
  mv   a1, s11
  jalr ra, 0(t1)
  mv   s10, a0
  mv   t0, s10
  mv   s9, t0
  j    .pand$lam0_match_end4
.pand$lam0_next15:
  call __lark_match_fail
.pand$lam0_match_end4:
  mv   a0, s9
  lw   s5, -12(s0)
  lw   s6, -16(s0)
  lw   s7, -20(s0)
  lw   s8, -24(s0)
  lw   s9, -28(s0)
  lw   s10, -32(s0)
  lw   s11, -36(s0)
  lw   ra, 44(sp)
  lw   s0, 40(sp)
  addi sp, sp, 48
  ret

.globl pand
pand:
  addi sp, sp, -32
  sw   ra, 28(sp)
  sw   s0, 24(sp)
  addi s0, sp, 32
  sw   s9, -12(s0)
  sw   s10, -16(s0)
  sw   s11, -20(s0)
  mv   s11, a0
  mv   s10, a1
  li   a0, 3
  call __heap_alloc
  mv   t3, a0
  la   t0, pand$lam0
  sw   t0, 0(t3)
  mv   t0, s10
  sw   t0, 4(t3)
  mv   t0, s11
  sw   t0, 8(t3)
  mv   s9, t3
  mv   a0, s9
  lw   s9, -12(s0)
  lw   s10, -16(s0)
  lw   s11, -20(s0)
  lw   ra, 28(sp)
  lw   s0, 24(sp)
  addi sp, sp, 32
  ret

.globl por$lam1
por$lam1:
  addi sp, sp, -48
  sw   ra, 44(sp)
  sw   s0, 40(sp)
  addi s0, sp, 48
  sw   s5, -12(s0)
  sw   s6, -16(s0)
  sw   s7, -20(s0)
  sw   s8, -24(s0)
  sw   s9, -28(s0)
  sw   s10, -32(s0)
  sw   s11, -36(s0)
  mv   s11, a0
  mv   s10, a1
  mv   t0, s11
  lw   t1, 4(t0)
  mv   s6, t1
  mv   t0, s11
  lw   t1, 8(t0)
  mv   s8, t1
  mv   t0, s6
  lw   t1, 0(t0)
  mv   a0, t0
  mv   a1, s10
  jalr ra, 0(t1)
  mv   s7, a0
  mv   t0, s7
  lw   t1, 0(t0)
  mv   s6, t1
  mv   t0, s6
  li   t1, 7  # tag 'Ok'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s5, t2
  mv   t0, s5
  bnez t0, .por$lam1_tag_ok9
  j    .por$lam1_next6
.por$lam1_tag_ok9:
  mv   t0, s7
  lw   t1, 4(t0)
  mv   s5, t1
  j    .por$lam1_sub11
.por$lam1_sub11:
  j    .por$lam1_arm5
.por$lam1_arm5:
  mv   t0, s7
  lw   t1, 4(t0)
  mv   s5, t1
  li   a0, 2
  call __heap_alloc
  mv   t3, a0
  li   t0, 7  # Ok
  sw   t0, 0(t3)
  mv   t0, s5
  sw   t0, 4(t3)
  mv   s11, t3
  mv   t0, s11
  mv   s9, t0
  j    .por$lam1_match_end4
.por$lam1_next6:
  mv   t0, s7
  lw   t1, 0(t0)
  mv   s11, t1
  mv   t0, s11
  li   t1, 3  # tag 'Err'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s5, t2
  mv   t0, s5
  bnez t0, .por$lam1_tag_ok18
  j    .por$lam1_next15
.por$lam1_tag_ok18:
  mv   t0, s7
  lw   t1, 4(t0)
  mv   s5, t1
  j    .por$lam1_sub20
.por$lam1_sub20:
  j    .por$lam1_arm14
.por$lam1_arm14:
  mv   t0, s7
  lw   t1, 4(t0)
  mv   s5, t1
  mv   t0, s8
  lw   t1, 0(t0)
  mv   a0, t0
  mv   a1, s10
  jalr ra, 0(t1)
  mv   s5, a0
  mv   t0, s5
  mv   s9, t0
  j    .por$lam1_match_end4
.por$lam1_next15:
  call __lark_match_fail
.por$lam1_match_end4:
  mv   a0, s9
  lw   s5, -12(s0)
  lw   s6, -16(s0)
  lw   s7, -20(s0)
  lw   s8, -24(s0)
  lw   s9, -28(s0)
  lw   s10, -32(s0)
  lw   s11, -36(s0)
  lw   ra, 44(sp)
  lw   s0, 40(sp)
  addi sp, sp, 48
  ret

.globl por
por:
  addi sp, sp, -32
  sw   ra, 28(sp)
  sw   s0, 24(sp)
  addi s0, sp, 32
  sw   s9, -12(s0)
  sw   s10, -16(s0)
  sw   s11, -20(s0)
  mv   s11, a0
  mv   s10, a1
  li   a0, 3
  call __heap_alloc
  mv   t3, a0
  la   t0, por$lam1
  sw   t0, 0(t3)
  mv   t0, s11
  sw   t0, 4(t3)
  mv   t0, s10
  sw   t0, 8(t3)
  mv   s9, t3
  mv   a0, s9
  lw   s9, -12(s0)
  lw   s10, -16(s0)
  lw   s11, -20(s0)
  lw   ra, 28(sp)
  lw   s0, 24(sp)
  addi sp, sp, 32
  ret

.globl p_factor
p_factor:
  addi sp, sp, -48
  sw   ra, 44(sp)
  sw   s0, 40(sp)
  addi s0, sp, 48
  sw   s5, -12(s0)
  sw   s6, -16(s0)
  sw   s7, -20(s0)
  sw   s8, -24(s0)
  sw   s9, -28(s0)
  sw   s10, -32(s0)
  sw   s11, -36(s0)
  mv   s11, a0
  mv   t0, s11
  lw   t1, 0(t0)
  mv   s9, t1
  mv   t0, s9
  li   t1, 1  # tag 'Cons'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s8, t2
  mv   t0, s8
  bnez t0, .p_factor_tag_ok6
  j    .p_factor_next3
.p_factor_tag_ok6:
  mv   t0, s11
  lw   t1, 4(t0)
  mv   s8, t1
  mv   t0, s8
  lw   t1, 0(t0)
  mv   s9, t1
  mv   t0, s9
  li   t1, 11  # tag 'TNum'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s7, t2
  mv   t0, s7
  bnez t0, .p_factor_tag_ok11
  j    .p_factor_next3
.p_factor_tag_ok11:
  mv   t0, s8
  lw   t1, 4(t0)
  mv   s7, t1
  j    .p_factor_sub13
.p_factor_sub13:
  j    .p_factor_sub8
.p_factor_sub8:
  mv   t0, s11
  lw   t1, 8(t0)
  mv   s8, t1
  j    .p_factor_sub15
.p_factor_sub15:
  j    .p_factor_arm2
.p_factor_arm2:
  mv   t0, s11
  lw   t1, 4(t0)
  mv   s7, t1
  mv   t0, s7
  lw   t1, 4(t0)
  mv   s9, t1
  mv   t0, s11
  lw   t1, 8(t0)
  mv   s7, t1
  li   a0, 2
  call __heap_alloc
  mv   t3, a0
  li   t0, 4  # Lit
  sw   t0, 0(t3)
  mv   t0, s9
  sw   t0, 4(t3)
  mv   s6, t3
  li   a0, 3
  call __heap_alloc
  mv   t3, a0
  li   t0, 0  # ()
  sw   t0, 0(t3)
  mv   t0, s6
  sw   t0, 4(t3)
  mv   t0, s7
  sw   t0, 8(t3)
  mv   s9, t3
  li   a0, 2
  call __heap_alloc
  mv   t3, a0
  li   t0, 7  # Ok
  sw   t0, 0(t3)
  mv   t0, s9
  sw   t0, 4(t3)
  mv   s6, t3
  mv   t0, s6
  mv   s8, t0
  j    .p_factor_match_end1
.p_factor_next3:
  mv   t0, s11
  lw   t1, 0(t0)
  mv   s6, t1
  mv   t0, s6
  li   t1, 1  # tag 'Cons'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s9, t2
  mv   t0, s9
  bnez t0, .p_factor_tag_ok26
  j    .p_factor_next23
.p_factor_tag_ok26:
  mv   t0, s11
  lw   t1, 4(t0)
  mv   s9, t1
  mv   t0, s9
  lw   t1, 0(t0)
  mv   s6, t1
  mv   t0, s6
  li   t1, 9  # tag 'TLParen'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s9, t2
  mv   t0, s9
  bnez t0, .p_factor_sub28
  j    .p_factor_next23
.p_factor_sub28:
  mv   t0, s11
  lw   t1, 8(t0)
  mv   s9, t1
  j    .p_factor_sub32
.p_factor_sub32:
  j    .p_factor_arm22
.p_factor_arm22:
  mv   t0, s11
  lw   t1, 4(t0)
  mv   s6, t1
  mv   t0, s11
  lw   t1, 8(t0)
  mv   s6, t1
  mv   a0, s6
  call p_expr
  mv   s9, a0
  mv   t0, s9
  lw   t1, 0(t0)
  mv   s6, t1
  mv   t0, s6
  li   t1, 3  # tag 'Err'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s7, t2
  mv   t0, s7
  bnez t0, .p_factor_tag_ok42
  j    .p_factor_next39
.p_factor_tag_ok42:
  mv   t0, s9
  lw   t1, 4(t0)
  mv   s7, t1
  j    .p_factor_sub44
.p_factor_sub44:
  j    .p_factor_arm38
.p_factor_arm38:
  mv   t0, s9
  lw   t1, 4(t0)
  mv   s7, t1
  li   a0, 2
  call __heap_alloc
  mv   t3, a0
  li   t0, 3  # Err
  sw   t0, 0(t3)
  mv   t0, s7
  sw   t0, 4(t3)
  mv   s11, t3
  mv   t0, s11
  mv   s10, t0
  j    .p_factor_match_end37
.p_factor_next39:
  mv   t0, s9
  lw   t1, 0(t0)
  mv   s11, t1
  mv   t0, s11
  li   t1, 7  # tag 'Ok'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s7, t2
  mv   t0, s7
  bnez t0, .p_factor_tag_ok51
  j    .p_factor_next48
.p_factor_tag_ok51:
  mv   t0, s9
  lw   t1, 4(t0)
  mv   s7, t1
  mv   t0, s7
  lw   t1, 4(t0)
  mv   s11, t1
  j    .p_factor_sub55
.p_factor_sub55:
  mv   t0, s7
  lw   t1, 8(t0)
  mv   s11, t1
  j    .p_factor_sub57
.p_factor_sub57:
  j    .p_factor_sub53
.p_factor_sub53:
  j    .p_factor_arm47
.p_factor_arm47:
  mv   t0, s9
  lw   t1, 4(t0)
  mv   s6, t1
  mv   t0, s6
  lw   t1, 4(t0)
  mv   s7, t1
  mv   t0, s6
  lw   t1, 8(t0)
  mv   s11, t1
  mv   t0, s11
  lw   t1, 0(t0)
  mv   s6, t1
  mv   t0, s6
  li   t1, 1  # tag 'Cons'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s5, t2
  mv   t0, s5
  bnez t0, .p_factor_tag_ok67
  j    .p_factor_next64
.p_factor_tag_ok67:
  mv   t0, s11
  lw   t1, 4(t0)
  mv   s5, t1
  mv   t0, s5
  lw   t1, 0(t0)
  mv   s9, t1
  mv   t0, s9
  li   t1, 13  # tag 'TRParen'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s5, t2
  mv   t0, s5
  bnez t0, .p_factor_sub69
  j    .p_factor_next64
.p_factor_sub69:
  mv   t0, s11
  lw   t1, 8(t0)
  mv   s5, t1
  j    .p_factor_sub73
.p_factor_sub73:
  j    .p_factor_arm63
.p_factor_arm63:
  mv   t0, s11
  lw   t1, 4(t0)
  mv   s9, t1
  mv   t0, s11
  lw   t1, 8(t0)
  mv   s9, t1
  li   a0, 3
  call __heap_alloc
  mv   t3, a0
  li   t0, 0  # ()
  sw   t0, 0(t3)
  mv   t0, s7
  sw   t0, 4(t3)
  mv   t0, s9
  sw   t0, 8(t3)
  mv   s6, t3
  li   a0, 2
  call __heap_alloc
  mv   t3, a0
  li   t0, 7  # Ok
  sw   t0, 0(t3)
  mv   t0, s6
  sw   t0, 4(t3)
  mv   s9, t3
  mv   t0, s9
  mv   s5, t0
  j    .p_factor_match_end62
.p_factor_next64:
  j    .p_factor_arm78
.p_factor_arm78:
  li   a0, 2
  call __heap_alloc
  mv   t3, a0
  li   t0, 3  # Err
  sw   t0, 0(t3)
  la   t0, .Lstr0
  sw   t0, 4(t3)
  mv   s11, t3
  mv   t0, s11
  mv   s5, t0
  j    .p_factor_match_end62
.p_factor_next79:
  call __lark_match_fail
.p_factor_match_end62:
  mv   t0, s5
  mv   s10, t0
  j    .p_factor_match_end37
.p_factor_next48:
  call __lark_match_fail
.p_factor_match_end37:
  mv   t0, s10
  mv   s8, t0
  j    .p_factor_match_end1
.p_factor_next23:
  j    .p_factor_arm81
.p_factor_arm81:
  li   a0, 2
  call __heap_alloc
  mv   t3, a0
  li   t0, 3  # Err
  sw   t0, 0(t3)
  la   t0, .Lstr1
  sw   t0, 4(t3)
  mv   s10, t3
  mv   t0, s10
  mv   s8, t0
  j    .p_factor_match_end1
.p_factor_next82:
  call __lark_match_fail
.p_factor_match_end1:
  mv   a0, s8
  lw   s5, -12(s0)
  lw   s6, -16(s0)
  lw   s7, -20(s0)
  lw   s8, -24(s0)
  lw   s9, -28(s0)
  lw   s10, -32(s0)
  lw   s11, -36(s0)
  lw   ra, 44(sp)
  lw   s0, 40(sp)
  addi sp, sp, 48
  ret

.globl p_term_tail$lam2
p_term_tail$lam2:
  addi sp, sp, -48
  sw   ra, 44(sp)
  sw   s0, 40(sp)
  addi s0, sp, 48
  sw   s4, -12(s0)
  sw   s5, -16(s0)
  sw   s6, -20(s0)
  sw   s7, -24(s0)
  sw   s8, -28(s0)
  sw   s9, -32(s0)
  sw   s10, -36(s0)
  sw   s11, -40(s0)
  mv   s11, a0
  mv   s10, a1
  mv   t0, s11
  lw   t1, 4(t0)
  mv   s7, t1
  mv   t0, s10
  lw   t1, 0(t0)
  mv   s6, t1
  mv   t0, s6
  li   t1, 1  # tag 'Cons'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s5, t2
  mv   t0, s5
  bnez t0, .p_term_tail$lam2_tag_ok7
  j    .p_term_tail$lam2_next4
.p_term_tail$lam2_tag_ok7:
  mv   t0, s10
  lw   t1, 4(t0)
  mv   s5, t1
  mv   t0, s5
  lw   t1, 0(t0)
  mv   s11, t1
  mv   t0, s11
  li   t1, 15  # tag 'TStar'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s5, t2
  mv   t0, s5
  bnez t0, .p_term_tail$lam2_sub9
  j    .p_term_tail$lam2_next4
.p_term_tail$lam2_sub9:
  mv   t0, s10
  lw   t1, 8(t0)
  mv   s5, t1
  j    .p_term_tail$lam2_sub13
.p_term_tail$lam2_sub13:
  j    .p_term_tail$lam2_arm3
.p_term_tail$lam2_arm3:
  mv   t0, s10
  lw   t1, 4(t0)
  mv   s11, t1
  mv   t0, s10
  lw   t1, 8(t0)
  mv   s11, t1
  mv   a0, s11
  call p_factor
  mv   s5, a0
  mv   t0, s5
  lw   t1, 0(t0)
  mv   s11, t1
  mv   t0, s11
  li   t1, 3  # tag 'Err'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s6, t2
  mv   t0, s6
  bnez t0, .p_term_tail$lam2_tag_ok23
  j    .p_term_tail$lam2_next20
.p_term_tail$lam2_tag_ok23:
  mv   t0, s5
  lw   t1, 4(t0)
  mv   s6, t1
  j    .p_term_tail$lam2_sub25
.p_term_tail$lam2_sub25:
  j    .p_term_tail$lam2_arm19
.p_term_tail$lam2_arm19:
  mv   t0, s5
  lw   t1, 4(t0)
  mv   s6, t1
  li   a0, 2
  call __heap_alloc
  mv   t3, a0
  li   t0, 3  # Err
  sw   t0, 0(t3)
  mv   t0, s6
  sw   t0, 4(t3)
  mv   s11, t3
  mv   t0, s11
  mv   s9, t0
  j    .p_term_tail$lam2_match_end18
.p_term_tail$lam2_next20:
  mv   t0, s5
  lw   t1, 0(t0)
  mv   s11, t1
  mv   t0, s11
  li   t1, 7  # tag 'Ok'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s6, t2
  mv   t0, s6
  bnez t0, .p_term_tail$lam2_tag_ok32
  j    .p_term_tail$lam2_next29
.p_term_tail$lam2_tag_ok32:
  mv   t0, s5
  lw   t1, 4(t0)
  mv   s6, t1
  mv   t0, s6
  lw   t1, 4(t0)
  mv   s11, t1
  j    .p_term_tail$lam2_sub36
.p_term_tail$lam2_sub36:
  mv   t0, s6
  lw   t1, 8(t0)
  mv   s11, t1
  j    .p_term_tail$lam2_sub38
.p_term_tail$lam2_sub38:
  j    .p_term_tail$lam2_sub34
.p_term_tail$lam2_sub34:
  j    .p_term_tail$lam2_arm28
.p_term_tail$lam2_arm28:
  mv   t0, s5
  lw   t1, 4(t0)
  mv   s6, t1
  mv   t0, s6
  lw   t1, 4(t0)
  mv   s11, t1
  mv   t0, s6
  lw   t1, 8(t0)
  mv   s4, t1
  li   a0, 3
  call __heap_alloc
  mv   t3, a0
  li   t0, 5  # Mul
  sw   t0, 0(t3)
  mv   t0, s7
  sw   t0, 4(t3)
  mv   t0, s11
  sw   t0, 8(t3)
  mv   s6, t3
  mv   a0, s6
  call p_term_tail
  mv   s11, a0
  mv   t0, s11
  lw   t1, 0(t0)
  mv   a0, t0
  mv   a1, s4
  jalr ra, 0(t1)
  mv   s6, a0
  mv   t0, s6
  mv   s9, t0
  j    .p_term_tail$lam2_match_end18
.p_term_tail$lam2_next29:
  call __lark_match_fail
.p_term_tail$lam2_match_end18:
  mv   t0, s9
  mv   s5, t0
  j    .p_term_tail$lam2_match_end2
.p_term_tail$lam2_next4:
  mv   t0, s10
  lw   t1, 0(t0)
  mv   s9, t1
  mv   t0, s9
  li   t1, 1  # tag 'Cons'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s6, t2
  mv   t0, s6
  bnez t0, .p_term_tail$lam2_tag_ok49
  j    .p_term_tail$lam2_next46
.p_term_tail$lam2_tag_ok49:
  mv   t0, s10
  lw   t1, 4(t0)
  mv   s6, t1
  mv   t0, s6
  lw   t1, 0(t0)
  mv   s9, t1
  mv   t0, s9
  li   t1, 14  # tag 'TSlash'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s6, t2
  mv   t0, s6
  bnez t0, .p_term_tail$lam2_sub51
  j    .p_term_tail$lam2_next46
.p_term_tail$lam2_sub51:
  mv   t0, s10
  lw   t1, 8(t0)
  mv   s6, t1
  j    .p_term_tail$lam2_sub55
.p_term_tail$lam2_sub55:
  j    .p_term_tail$lam2_arm45
.p_term_tail$lam2_arm45:
  mv   t0, s10
  lw   t1, 4(t0)
  mv   s9, t1
  mv   t0, s10
  lw   t1, 8(t0)
  mv   s9, t1
  mv   a0, s9
  call p_factor
  mv   s6, a0
  mv   t0, s6
  lw   t1, 0(t0)
  mv   s9, t1
  mv   t0, s9
  li   t1, 3  # tag 'Err'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s11, t2
  mv   t0, s11
  bnez t0, .p_term_tail$lam2_tag_ok65
  j    .p_term_tail$lam2_next62
.p_term_tail$lam2_tag_ok65:
  mv   t0, s6
  lw   t1, 4(t0)
  mv   s11, t1
  j    .p_term_tail$lam2_sub67
.p_term_tail$lam2_sub67:
  j    .p_term_tail$lam2_arm61
.p_term_tail$lam2_arm61:
  mv   t0, s6
  lw   t1, 4(t0)
  mv   s11, t1
  li   a0, 2
  call __heap_alloc
  mv   t3, a0
  li   t0, 3  # Err
  sw   t0, 0(t3)
  mv   t0, s11
  sw   t0, 4(t3)
  mv   s9, t3
  mv   t0, s9
  mv   s8, t0
  j    .p_term_tail$lam2_match_end60
.p_term_tail$lam2_next62:
  mv   t0, s6
  lw   t1, 0(t0)
  mv   s9, t1
  mv   t0, s9
  li   t1, 7  # tag 'Ok'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s11, t2
  mv   t0, s11
  bnez t0, .p_term_tail$lam2_tag_ok74
  j    .p_term_tail$lam2_next71
.p_term_tail$lam2_tag_ok74:
  mv   t0, s6
  lw   t1, 4(t0)
  mv   s11, t1
  mv   t0, s11
  lw   t1, 4(t0)
  mv   s9, t1
  j    .p_term_tail$lam2_sub78
.p_term_tail$lam2_sub78:
  mv   t0, s11
  lw   t1, 8(t0)
  mv   s9, t1
  j    .p_term_tail$lam2_sub80
.p_term_tail$lam2_sub80:
  j    .p_term_tail$lam2_sub76
.p_term_tail$lam2_sub76:
  j    .p_term_tail$lam2_arm70
.p_term_tail$lam2_arm70:
  mv   t0, s6
  lw   t1, 4(t0)
  mv   s11, t1
  mv   t0, s11
  lw   t1, 4(t0)
  mv   s9, t1
  mv   t0, s11
  lw   t1, 8(t0)
  mv   s4, t1
  li   a0, 3
  call __heap_alloc
  mv   t3, a0
  li   t0, 2  # Div
  sw   t0, 0(t3)
  mv   t0, s7
  sw   t0, 4(t3)
  mv   t0, s9
  sw   t0, 8(t3)
  mv   s11, t3
  mv   a0, s11
  call p_term_tail
  mv   s9, a0
  mv   t0, s9
  lw   t1, 0(t0)
  mv   a0, t0
  mv   a1, s4
  jalr ra, 0(t1)
  mv   s11, a0
  mv   t0, s11
  mv   s8, t0
  j    .p_term_tail$lam2_match_end60
.p_term_tail$lam2_next71:
  call __lark_match_fail
.p_term_tail$lam2_match_end60:
  mv   t0, s8
  mv   s5, t0
  j    .p_term_tail$lam2_match_end2
.p_term_tail$lam2_next46:
  j    .p_term_tail$lam2_arm87
.p_term_tail$lam2_arm87:
  li   a0, 3
  call __heap_alloc
  mv   t3, a0
  li   t0, 0  # ()
  sw   t0, 0(t3)
  mv   t0, s7
  sw   t0, 4(t3)
  mv   t0, s10
  sw   t0, 8(t3)
  mv   s8, t3
  li   a0, 2
  call __heap_alloc
  mv   t3, a0
  li   t0, 7  # Ok
  sw   t0, 0(t3)
  mv   t0, s8
  sw   t0, 4(t3)
  mv   s6, t3
  mv   t0, s6
  mv   s5, t0
  j    .p_term_tail$lam2_match_end2
.p_term_tail$lam2_next88:
  call __lark_match_fail
.p_term_tail$lam2_match_end2:
  mv   a0, s5
  lw   s4, -12(s0)
  lw   s5, -16(s0)
  lw   s6, -20(s0)
  lw   s7, -24(s0)
  lw   s8, -28(s0)
  lw   s9, -32(s0)
  lw   s10, -36(s0)
  lw   s11, -40(s0)
  lw   ra, 44(sp)
  lw   s0, 40(sp)
  addi sp, sp, 48
  ret

.globl p_term_tail
p_term_tail:
  addi sp, sp, -16
  sw   ra, 12(sp)
  sw   s0, 8(sp)
  addi s0, sp, 16
  sw   s10, -12(s0)
  sw   s11, -16(s0)
  mv   s11, a0
  li   a0, 2
  call __heap_alloc
  mv   t3, a0
  la   t0, p_term_tail$lam2
  sw   t0, 0(t3)
  mv   t0, s11
  sw   t0, 4(t3)
  mv   s10, t3
  mv   a0, s10
  lw   s10, -12(s0)
  lw   s11, -16(s0)
  lw   ra, 12(sp)
  lw   s0, 8(sp)
  addi sp, sp, 16
  ret

.globl p_term
p_term:
  addi sp, sp, -32
  sw   ra, 28(sp)
  sw   s0, 24(sp)
  addi s0, sp, 32
  sw   s7, -12(s0)
  sw   s8, -16(s0)
  sw   s9, -20(s0)
  sw   s10, -24(s0)
  sw   s11, -28(s0)
  mv   s11, a0
  mv   a0, s11
  call p_factor
  mv   s9, a0
  mv   t0, s9
  lw   t1, 0(t0)
  mv   s8, t1
  mv   t0, s8
  li   t1, 3  # tag 'Err'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s7, t2
  mv   t0, s7
  bnez t0, .p_term_tag_ok7
  j    .p_term_next4
.p_term_tag_ok7:
  mv   t0, s9
  lw   t1, 4(t0)
  mv   s7, t1
  j    .p_term_sub9
.p_term_sub9:
  j    .p_term_arm3
.p_term_arm3:
  mv   t0, s9
  lw   t1, 4(t0)
  mv   s7, t1
  li   a0, 2
  call __heap_alloc
  mv   t3, a0
  li   t0, 3  # Err
  sw   t0, 0(t3)
  mv   t0, s7
  sw   t0, 4(t3)
  mv   s11, t3
  mv   t0, s11
  mv   s10, t0
  j    .p_term_match_end2
.p_term_next4:
  mv   t0, s9
  lw   t1, 0(t0)
  mv   s11, t1
  mv   t0, s11
  li   t1, 7  # tag 'Ok'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s7, t2
  mv   t0, s7
  bnez t0, .p_term_tag_ok16
  j    .p_term_next13
.p_term_tag_ok16:
  mv   t0, s9
  lw   t1, 4(t0)
  mv   s7, t1
  mv   t0, s7
  lw   t1, 4(t0)
  mv   s11, t1
  j    .p_term_sub20
.p_term_sub20:
  mv   t0, s7
  lw   t1, 8(t0)
  mv   s11, t1
  j    .p_term_sub22
.p_term_sub22:
  j    .p_term_sub18
.p_term_sub18:
  j    .p_term_arm12
.p_term_arm12:
  mv   t0, s9
  lw   t1, 4(t0)
  mv   s7, t1
  mv   t0, s7
  lw   t1, 4(t0)
  mv   s11, t1
  mv   t0, s7
  lw   t1, 8(t0)
  mv   s8, t1
  mv   a0, s11
  call p_term_tail
  mv   s7, a0
  mv   t0, s7
  lw   t1, 0(t0)
  mv   a0, t0
  mv   a1, s8
  jalr ra, 0(t1)
  mv   s11, a0
  mv   t0, s11
  mv   s10, t0
  j    .p_term_match_end2
.p_term_next13:
  call __lark_match_fail
.p_term_match_end2:
  mv   a0, s10
  lw   s7, -12(s0)
  lw   s8, -16(s0)
  lw   s9, -20(s0)
  lw   s10, -24(s0)
  lw   s11, -28(s0)
  lw   ra, 28(sp)
  lw   s0, 24(sp)
  addi sp, sp, 32
  ret

.globl p_expr_tail$lam3
p_expr_tail$lam3:
  addi sp, sp, -48
  sw   ra, 44(sp)
  sw   s0, 40(sp)
  addi s0, sp, 48
  sw   s4, -12(s0)
  sw   s5, -16(s0)
  sw   s6, -20(s0)
  sw   s7, -24(s0)
  sw   s8, -28(s0)
  sw   s9, -32(s0)
  sw   s10, -36(s0)
  sw   s11, -40(s0)
  mv   s11, a0
  mv   s10, a1
  mv   t0, s11
  lw   t1, 4(t0)
  mv   s7, t1
  mv   t0, s10
  lw   t1, 0(t0)
  mv   s6, t1
  mv   t0, s6
  li   t1, 1  # tag 'Cons'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s5, t2
  mv   t0, s5
  bnez t0, .p_expr_tail$lam3_tag_ok7
  j    .p_expr_tail$lam3_next4
.p_expr_tail$lam3_tag_ok7:
  mv   t0, s10
  lw   t1, 4(t0)
  mv   s5, t1
  mv   t0, s5
  lw   t1, 0(t0)
  mv   s11, t1
  mv   t0, s11
  li   t1, 12  # tag 'TPlus'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s5, t2
  mv   t0, s5
  bnez t0, .p_expr_tail$lam3_sub9
  j    .p_expr_tail$lam3_next4
.p_expr_tail$lam3_sub9:
  mv   t0, s10
  lw   t1, 8(t0)
  mv   s5, t1
  j    .p_expr_tail$lam3_sub13
.p_expr_tail$lam3_sub13:
  j    .p_expr_tail$lam3_arm3
.p_expr_tail$lam3_arm3:
  mv   t0, s10
  lw   t1, 4(t0)
  mv   s11, t1
  mv   t0, s10
  lw   t1, 8(t0)
  mv   s11, t1
  mv   a0, s11
  call p_term
  mv   s5, a0
  mv   t0, s5
  lw   t1, 0(t0)
  mv   s11, t1
  mv   t0, s11
  li   t1, 3  # tag 'Err'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s6, t2
  mv   t0, s6
  bnez t0, .p_expr_tail$lam3_tag_ok23
  j    .p_expr_tail$lam3_next20
.p_expr_tail$lam3_tag_ok23:
  mv   t0, s5
  lw   t1, 4(t0)
  mv   s6, t1
  j    .p_expr_tail$lam3_sub25
.p_expr_tail$lam3_sub25:
  j    .p_expr_tail$lam3_arm19
.p_expr_tail$lam3_arm19:
  mv   t0, s5
  lw   t1, 4(t0)
  mv   s6, t1
  li   a0, 2
  call __heap_alloc
  mv   t3, a0
  li   t0, 3  # Err
  sw   t0, 0(t3)
  mv   t0, s6
  sw   t0, 4(t3)
  mv   s11, t3
  mv   t0, s11
  mv   s9, t0
  j    .p_expr_tail$lam3_match_end18
.p_expr_tail$lam3_next20:
  mv   t0, s5
  lw   t1, 0(t0)
  mv   s11, t1
  mv   t0, s11
  li   t1, 7  # tag 'Ok'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s6, t2
  mv   t0, s6
  bnez t0, .p_expr_tail$lam3_tag_ok32
  j    .p_expr_tail$lam3_next29
.p_expr_tail$lam3_tag_ok32:
  mv   t0, s5
  lw   t1, 4(t0)
  mv   s6, t1
  mv   t0, s6
  lw   t1, 4(t0)
  mv   s11, t1
  j    .p_expr_tail$lam3_sub36
.p_expr_tail$lam3_sub36:
  mv   t0, s6
  lw   t1, 8(t0)
  mv   s11, t1
  j    .p_expr_tail$lam3_sub38
.p_expr_tail$lam3_sub38:
  j    .p_expr_tail$lam3_sub34
.p_expr_tail$lam3_sub34:
  j    .p_expr_tail$lam3_arm28
.p_expr_tail$lam3_arm28:
  mv   t0, s5
  lw   t1, 4(t0)
  mv   s6, t1
  mv   t0, s6
  lw   t1, 4(t0)
  mv   s11, t1
  mv   t0, s6
  lw   t1, 8(t0)
  mv   s4, t1
  li   a0, 3
  call __heap_alloc
  mv   t3, a0
  li   t0, 0  # Add
  sw   t0, 0(t3)
  mv   t0, s7
  sw   t0, 4(t3)
  mv   t0, s11
  sw   t0, 8(t3)
  mv   s6, t3
  mv   a0, s6
  call p_expr_tail
  mv   s11, a0
  mv   t0, s11
  lw   t1, 0(t0)
  mv   a0, t0
  mv   a1, s4
  jalr ra, 0(t1)
  mv   s6, a0
  mv   t0, s6
  mv   s9, t0
  j    .p_expr_tail$lam3_match_end18
.p_expr_tail$lam3_next29:
  call __lark_match_fail
.p_expr_tail$lam3_match_end18:
  mv   t0, s9
  mv   s5, t0
  j    .p_expr_tail$lam3_match_end2
.p_expr_tail$lam3_next4:
  mv   t0, s10
  lw   t1, 0(t0)
  mv   s9, t1
  mv   t0, s9
  li   t1, 1  # tag 'Cons'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s6, t2
  mv   t0, s6
  bnez t0, .p_expr_tail$lam3_tag_ok49
  j    .p_expr_tail$lam3_next46
.p_expr_tail$lam3_tag_ok49:
  mv   t0, s10
  lw   t1, 4(t0)
  mv   s6, t1
  mv   t0, s6
  lw   t1, 0(t0)
  mv   s9, t1
  mv   t0, s9
  li   t1, 10  # tag 'TMinus'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s6, t2
  mv   t0, s6
  bnez t0, .p_expr_tail$lam3_sub51
  j    .p_expr_tail$lam3_next46
.p_expr_tail$lam3_sub51:
  mv   t0, s10
  lw   t1, 8(t0)
  mv   s6, t1
  j    .p_expr_tail$lam3_sub55
.p_expr_tail$lam3_sub55:
  j    .p_expr_tail$lam3_arm45
.p_expr_tail$lam3_arm45:
  mv   t0, s10
  lw   t1, 4(t0)
  mv   s9, t1
  mv   t0, s10
  lw   t1, 8(t0)
  mv   s9, t1
  mv   a0, s9
  call p_term
  mv   s6, a0
  mv   t0, s6
  lw   t1, 0(t0)
  mv   s9, t1
  mv   t0, s9
  li   t1, 3  # tag 'Err'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s11, t2
  mv   t0, s11
  bnez t0, .p_expr_tail$lam3_tag_ok65
  j    .p_expr_tail$lam3_next62
.p_expr_tail$lam3_tag_ok65:
  mv   t0, s6
  lw   t1, 4(t0)
  mv   s11, t1
  j    .p_expr_tail$lam3_sub67
.p_expr_tail$lam3_sub67:
  j    .p_expr_tail$lam3_arm61
.p_expr_tail$lam3_arm61:
  mv   t0, s6
  lw   t1, 4(t0)
  mv   s11, t1
  li   a0, 2
  call __heap_alloc
  mv   t3, a0
  li   t0, 3  # Err
  sw   t0, 0(t3)
  mv   t0, s11
  sw   t0, 4(t3)
  mv   s9, t3
  mv   t0, s9
  mv   s8, t0
  j    .p_expr_tail$lam3_match_end60
.p_expr_tail$lam3_next62:
  mv   t0, s6
  lw   t1, 0(t0)
  mv   s9, t1
  mv   t0, s9
  li   t1, 7  # tag 'Ok'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s11, t2
  mv   t0, s11
  bnez t0, .p_expr_tail$lam3_tag_ok74
  j    .p_expr_tail$lam3_next71
.p_expr_tail$lam3_tag_ok74:
  mv   t0, s6
  lw   t1, 4(t0)
  mv   s11, t1
  mv   t0, s11
  lw   t1, 4(t0)
  mv   s9, t1
  j    .p_expr_tail$lam3_sub78
.p_expr_tail$lam3_sub78:
  mv   t0, s11
  lw   t1, 8(t0)
  mv   s9, t1
  j    .p_expr_tail$lam3_sub80
.p_expr_tail$lam3_sub80:
  j    .p_expr_tail$lam3_sub76
.p_expr_tail$lam3_sub76:
  j    .p_expr_tail$lam3_arm70
.p_expr_tail$lam3_arm70:
  mv   t0, s6
  lw   t1, 4(t0)
  mv   s11, t1
  mv   t0, s11
  lw   t1, 4(t0)
  mv   s9, t1
  mv   t0, s11
  lw   t1, 8(t0)
  mv   s4, t1
  li   a0, 3
  call __heap_alloc
  mv   t3, a0
  li   t0, 8  # Sub
  sw   t0, 0(t3)
  mv   t0, s7
  sw   t0, 4(t3)
  mv   t0, s9
  sw   t0, 8(t3)
  mv   s11, t3
  mv   a0, s11
  call p_expr_tail
  mv   s9, a0
  mv   t0, s9
  lw   t1, 0(t0)
  mv   a0, t0
  mv   a1, s4
  jalr ra, 0(t1)
  mv   s11, a0
  mv   t0, s11
  mv   s8, t0
  j    .p_expr_tail$lam3_match_end60
.p_expr_tail$lam3_next71:
  call __lark_match_fail
.p_expr_tail$lam3_match_end60:
  mv   t0, s8
  mv   s5, t0
  j    .p_expr_tail$lam3_match_end2
.p_expr_tail$lam3_next46:
  j    .p_expr_tail$lam3_arm87
.p_expr_tail$lam3_arm87:
  li   a0, 3
  call __heap_alloc
  mv   t3, a0
  li   t0, 0  # ()
  sw   t0, 0(t3)
  mv   t0, s7
  sw   t0, 4(t3)
  mv   t0, s10
  sw   t0, 8(t3)
  mv   s8, t3
  li   a0, 2
  call __heap_alloc
  mv   t3, a0
  li   t0, 7  # Ok
  sw   t0, 0(t3)
  mv   t0, s8
  sw   t0, 4(t3)
  mv   s6, t3
  mv   t0, s6
  mv   s5, t0
  j    .p_expr_tail$lam3_match_end2
.p_expr_tail$lam3_next88:
  call __lark_match_fail
.p_expr_tail$lam3_match_end2:
  mv   a0, s5
  lw   s4, -12(s0)
  lw   s5, -16(s0)
  lw   s6, -20(s0)
  lw   s7, -24(s0)
  lw   s8, -28(s0)
  lw   s9, -32(s0)
  lw   s10, -36(s0)
  lw   s11, -40(s0)
  lw   ra, 44(sp)
  lw   s0, 40(sp)
  addi sp, sp, 48
  ret

.globl p_expr_tail
p_expr_tail:
  addi sp, sp, -16
  sw   ra, 12(sp)
  sw   s0, 8(sp)
  addi s0, sp, 16
  sw   s10, -12(s0)
  sw   s11, -16(s0)
  mv   s11, a0
  li   a0, 2
  call __heap_alloc
  mv   t3, a0
  la   t0, p_expr_tail$lam3
  sw   t0, 0(t3)
  mv   t0, s11
  sw   t0, 4(t3)
  mv   s10, t3
  mv   a0, s10
  lw   s10, -12(s0)
  lw   s11, -16(s0)
  lw   ra, 12(sp)
  lw   s0, 8(sp)
  addi sp, sp, 16
  ret

.globl p_expr$lam4
p_expr$lam4:
  addi sp, sp, -32
  sw   ra, 28(sp)
  sw   s0, 24(sp)
  addi s0, sp, 32
  sw   s9, -12(s0)
  sw   s10, -16(s0)
  sw   s11, -20(s0)
  mv   s11, a0
  mv   s10, a1
  mv   a0, s10
  call p_term
  mv   s9, a0
  mv   a0, s9
  lw   s9, -12(s0)
  lw   s10, -16(s0)
  lw   s11, -20(s0)
  lw   ra, 28(sp)
  lw   s0, 24(sp)
  addi sp, sp, 32
  ret

.globl p_expr$lam5$lam6
p_expr$lam5$lam6:
  addi sp, sp, -32
  sw   ra, 28(sp)
  sw   s0, 24(sp)
  addi s0, sp, 32
  sw   s8, -12(s0)
  sw   s9, -16(s0)
  sw   s10, -20(s0)
  sw   s11, -24(s0)
  mv   s11, a0
  mv   s10, a1
  mv   t0, s11
  lw   t1, 4(t0)
  mv   s9, t1
  mv   a0, s9
  call p_expr_tail
  mv   s8, a0
  mv   t0, s8
  lw   t1, 0(t0)
  mv   a0, t0
  mv   a1, s10
  jalr ra, 0(t1)
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

.globl p_expr$lam5
p_expr$lam5:
  addi sp, sp, -32
  sw   ra, 28(sp)
  sw   s0, 24(sp)
  addi s0, sp, 32
  sw   s9, -12(s0)
  sw   s10, -16(s0)
  sw   s11, -20(s0)
  mv   s11, a0
  mv   s10, a1
  li   a0, 2
  call __heap_alloc
  mv   t3, a0
  la   t0, p_expr$lam5$lam6
  sw   t0, 0(t3)
  mv   t0, s10
  sw   t0, 4(t3)
  mv   s9, t3
  mv   a0, s9
  lw   s9, -12(s0)
  lw   s10, -16(s0)
  lw   s11, -20(s0)
  lw   ra, 28(sp)
  lw   s0, 24(sp)
  addi sp, sp, 32
  ret

.globl p_expr
p_expr:
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
  la   t0, p_expr$lam4
  sw   t0, 0(t3)
  mv   s10, t3
  li   a0, 1
  call __heap_alloc
  mv   t3, a0
  la   t0, p_expr$lam5
  sw   t0, 0(t3)
  mv   s9, t3
  mv   a0, s10
  mv   a1, s9
  call pand
  mv   s8, a0
  mv   t0, s8
  lw   t1, 0(t0)
  mv   a0, t0
  mv   a1, s11
  jalr ra, 0(t1)
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

.globl eval
eval:
  addi sp, sp, -32
  sw   ra, 28(sp)
  sw   s0, 24(sp)
  addi s0, sp, 32
  sw   s7, -12(s0)
  sw   s8, -16(s0)
  sw   s9, -20(s0)
  sw   s10, -24(s0)
  sw   s11, -28(s0)
  mv   s11, a0
  mv   t0, s11
  lw   t1, 0(t0)
  mv   s9, t1
  mv   t0, s9
  li   t1, 4  # tag 'Lit'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s8, t2
  mv   t0, s8
  bnez t0, .eval_tag_ok6
  j    .eval_next3
.eval_tag_ok6:
  mv   t0, s11
  lw   t1, 4(t0)
  mv   s8, t1
  j    .eval_sub8
.eval_sub8:
  j    .eval_arm2
.eval_arm2:
  mv   t0, s11
  lw   t1, 4(t0)
  mv   s8, t1
  mv   t0, s8
  mv   s10, t0
  j    .eval_match_end1
.eval_next3:
  mv   t0, s11
  lw   t1, 0(t0)
  mv   s8, t1
  mv   t0, s8
  li   t1, 0  # tag 'Add'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s9, t2
  mv   t0, s9
  bnez t0, .eval_tag_ok14
  j    .eval_next11
.eval_tag_ok14:
  mv   t0, s11
  lw   t1, 4(t0)
  mv   s9, t1
  j    .eval_sub16
.eval_sub16:
  mv   t0, s11
  lw   t1, 8(t0)
  mv   s9, t1
  j    .eval_sub18
.eval_sub18:
  j    .eval_arm10
.eval_arm10:
  mv   t0, s11
  lw   t1, 4(t0)
  mv   s9, t1
  mv   t0, s11
  lw   t1, 8(t0)
  mv   s8, t1
  mv   a0, s9
  call eval
  mv   s7, a0
  mv   a0, s8
  call eval
  mv   s9, a0
  mv   t0, s7
  mv   t1, s9
  add  t2, t0, t1
  mv   s8, t2
  mv   t0, s8
  mv   s10, t0
  j    .eval_match_end1
.eval_next11:
  mv   t0, s11
  lw   t1, 0(t0)
  mv   s8, t1
  mv   t0, s8
  li   t1, 8  # tag 'Sub'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s9, t2
  mv   t0, s9
  bnez t0, .eval_tag_ok28
  j    .eval_next25
.eval_tag_ok28:
  mv   t0, s11
  lw   t1, 4(t0)
  mv   s9, t1
  j    .eval_sub30
.eval_sub30:
  mv   t0, s11
  lw   t1, 8(t0)
  mv   s9, t1
  j    .eval_sub32
.eval_sub32:
  j    .eval_arm24
.eval_arm24:
  mv   t0, s11
  lw   t1, 4(t0)
  mv   s9, t1
  mv   t0, s11
  lw   t1, 8(t0)
  mv   s8, t1
  mv   a0, s9
  call eval
  mv   s7, a0
  mv   a0, s8
  call eval
  mv   s9, a0
  mv   t0, s7
  mv   t1, s9
  sub  t2, t0, t1
  mv   s8, t2
  mv   t0, s8
  mv   s10, t0
  j    .eval_match_end1
.eval_next25:
  mv   t0, s11
  lw   t1, 0(t0)
  mv   s8, t1
  mv   t0, s8
  li   t1, 5  # tag 'Mul'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s9, t2
  mv   t0, s9
  bnez t0, .eval_tag_ok42
  j    .eval_next39
.eval_tag_ok42:
  mv   t0, s11
  lw   t1, 4(t0)
  mv   s9, t1
  j    .eval_sub44
.eval_sub44:
  mv   t0, s11
  lw   t1, 8(t0)
  mv   s9, t1
  j    .eval_sub46
.eval_sub46:
  j    .eval_arm38
.eval_arm38:
  mv   t0, s11
  lw   t1, 4(t0)
  mv   s9, t1
  mv   t0, s11
  lw   t1, 8(t0)
  mv   s8, t1
  mv   a0, s9
  call eval
  mv   s7, a0
  mv   a0, s8
  call eval
  mv   s9, a0
  mv   t0, s7
  mv   t1, s9
  mul  t2, t0, t1
  mv   s8, t2
  mv   t0, s8
  mv   s10, t0
  j    .eval_match_end1
.eval_next39:
  mv   t0, s11
  lw   t1, 0(t0)
  mv   s8, t1
  mv   t0, s8
  li   t1, 2  # tag 'Div'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s9, t2
  mv   t0, s9
  bnez t0, .eval_tag_ok56
  j    .eval_next53
.eval_tag_ok56:
  mv   t0, s11
  lw   t1, 4(t0)
  mv   s9, t1
  j    .eval_sub58
.eval_sub58:
  mv   t0, s11
  lw   t1, 8(t0)
  mv   s9, t1
  j    .eval_sub60
.eval_sub60:
  j    .eval_arm52
.eval_arm52:
  mv   t0, s11
  lw   t1, 4(t0)
  mv   s9, t1
  mv   t0, s11
  lw   t1, 8(t0)
  mv   s8, t1
  mv   a0, s9
  call eval
  mv   s7, a0
  mv   a0, s8
  call eval
  mv   s9, a0
  mv   t0, s7
  mv   t1, s9
  div  t2, t0, t1
  mv   s8, t2
  mv   t0, s8
  mv   s10, t0
  j    .eval_match_end1
.eval_next53:
  call __lark_match_fail
.eval_match_end1:
  mv   a0, s10
  lw   s7, -12(s0)
  lw   s8, -16(s0)
  lw   s9, -20(s0)
  lw   s10, -24(s0)
  lw   s11, -28(s0)
  lw   ra, 28(sp)
  lw   s0, 24(sp)
  addi sp, sp, 32
  ret

.globl pretty
pretty:
  addi sp, sp, -32
  sw   ra, 28(sp)
  sw   s0, 24(sp)
  addi s0, sp, 32
  sw   s7, -12(s0)
  sw   s8, -16(s0)
  sw   s9, -20(s0)
  sw   s10, -24(s0)
  sw   s11, -28(s0)
  mv   s11, a0
  mv   t0, s11
  lw   t1, 0(t0)
  mv   s9, t1
  mv   t0, s9
  li   t1, 4  # tag 'Lit'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s8, t2
  mv   t0, s8
  bnez t0, .pretty_tag_ok6
  j    .pretty_next3
.pretty_tag_ok6:
  mv   t0, s11
  lw   t1, 4(t0)
  mv   s8, t1
  j    .pretty_sub8
.pretty_sub8:
  j    .pretty_arm2
.pretty_arm2:
  mv   t0, s11
  lw   t1, 4(t0)
  mv   s8, t1
  mv   a0, s8
  call show
  mv   s9, a0
  mv   t0, s9
  mv   s10, t0
  j    .pretty_match_end1
.pretty_next3:
  mv   t0, s11
  lw   t1, 0(t0)
  mv   s9, t1
  mv   t0, s9
  li   t1, 0  # tag 'Add'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s8, t2
  mv   t0, s8
  bnez t0, .pretty_tag_ok15
  j    .pretty_next12
.pretty_tag_ok15:
  mv   t0, s11
  lw   t1, 4(t0)
  mv   s8, t1
  j    .pretty_sub17
.pretty_sub17:
  mv   t0, s11
  lw   t1, 8(t0)
  mv   s8, t1
  j    .pretty_sub19
.pretty_sub19:
  j    .pretty_arm11
.pretty_arm11:
  mv   t0, s11
  lw   t1, 4(t0)
  mv   s8, t1
  mv   t0, s11
  lw   t1, 8(t0)
  mv   s9, t1
  mv   a0, s8
  call pretty
  mv   s7, a0
  la   a0, .Lstr2
  mv   a1, s7
  call __str_concat
  mv   s8, a0
  mv   a0, s8
  la   a1, .Lstr3
  call __str_concat
  mv   s7, a0
  mv   a0, s9
  call pretty
  mv   s8, a0
  mv   a0, s7
  mv   a1, s8
  call __str_concat
  mv   s9, a0
  mv   a0, s9
  la   a1, .Lstr4
  call __str_concat
  mv   s8, a0
  mv   t0, s8
  mv   s10, t0
  j    .pretty_match_end1
.pretty_next12:
  mv   t0, s11
  lw   t1, 0(t0)
  mv   s8, t1
  mv   t0, s8
  li   t1, 8  # tag 'Sub'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s9, t2
  mv   t0, s9
  bnez t0, .pretty_tag_ok32
  j    .pretty_next29
.pretty_tag_ok32:
  mv   t0, s11
  lw   t1, 4(t0)
  mv   s9, t1
  j    .pretty_sub34
.pretty_sub34:
  mv   t0, s11
  lw   t1, 8(t0)
  mv   s9, t1
  j    .pretty_sub36
.pretty_sub36:
  j    .pretty_arm28
.pretty_arm28:
  mv   t0, s11
  lw   t1, 4(t0)
  mv   s9, t1
  mv   t0, s11
  lw   t1, 8(t0)
  mv   s8, t1
  mv   a0, s9
  call pretty
  mv   s7, a0
  la   a0, .Lstr2
  mv   a1, s7
  call __str_concat
  mv   s9, a0
  mv   a0, s9
  la   a1, .Lstr5
  call __str_concat
  mv   s7, a0
  mv   a0, s8
  call pretty
  mv   s9, a0
  mv   a0, s7
  mv   a1, s9
  call __str_concat
  mv   s8, a0
  mv   a0, s8
  la   a1, .Lstr4
  call __str_concat
  mv   s9, a0
  mv   t0, s9
  mv   s10, t0
  j    .pretty_match_end1
.pretty_next29:
  mv   t0, s11
  lw   t1, 0(t0)
  mv   s9, t1
  mv   t0, s9
  li   t1, 5  # tag 'Mul'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s8, t2
  mv   t0, s8
  bnez t0, .pretty_tag_ok49
  j    .pretty_next46
.pretty_tag_ok49:
  mv   t0, s11
  lw   t1, 4(t0)
  mv   s8, t1
  j    .pretty_sub51
.pretty_sub51:
  mv   t0, s11
  lw   t1, 8(t0)
  mv   s8, t1
  j    .pretty_sub53
.pretty_sub53:
  j    .pretty_arm45
.pretty_arm45:
  mv   t0, s11
  lw   t1, 4(t0)
  mv   s8, t1
  mv   t0, s11
  lw   t1, 8(t0)
  mv   s9, t1
  mv   a0, s8
  call pretty
  mv   s7, a0
  la   a0, .Lstr2
  mv   a1, s7
  call __str_concat
  mv   s8, a0
  mv   a0, s8
  la   a1, .Lstr6
  call __str_concat
  mv   s7, a0
  mv   a0, s9
  call pretty
  mv   s8, a0
  mv   a0, s7
  mv   a1, s8
  call __str_concat
  mv   s9, a0
  mv   a0, s9
  la   a1, .Lstr4
  call __str_concat
  mv   s8, a0
  mv   t0, s8
  mv   s10, t0
  j    .pretty_match_end1
.pretty_next46:
  mv   t0, s11
  lw   t1, 0(t0)
  mv   s8, t1
  mv   t0, s8
  li   t1, 2  # tag 'Div'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s9, t2
  mv   t0, s9
  bnez t0, .pretty_tag_ok66
  j    .pretty_next63
.pretty_tag_ok66:
  mv   t0, s11
  lw   t1, 4(t0)
  mv   s9, t1
  j    .pretty_sub68
.pretty_sub68:
  mv   t0, s11
  lw   t1, 8(t0)
  mv   s9, t1
  j    .pretty_sub70
.pretty_sub70:
  j    .pretty_arm62
.pretty_arm62:
  mv   t0, s11
  lw   t1, 4(t0)
  mv   s9, t1
  mv   t0, s11
  lw   t1, 8(t0)
  mv   s8, t1
  mv   a0, s9
  call pretty
  mv   s7, a0
  la   a0, .Lstr2
  mv   a1, s7
  call __str_concat
  mv   s9, a0
  mv   a0, s9
  la   a1, .Lstr7
  call __str_concat
  mv   s7, a0
  mv   a0, s8
  call pretty
  mv   s9, a0
  mv   a0, s7
  mv   a1, s9
  call __str_concat
  mv   s8, a0
  mv   a0, s8
  la   a1, .Lstr4
  call __str_concat
  mv   s9, a0
  mv   t0, s9
  mv   s10, t0
  j    .pretty_match_end1
.pretty_next63:
  call __lark_match_fail
.pretty_match_end1:
  mv   a0, s10
  lw   s7, -12(s0)
  lw   s8, -16(s0)
  lw   s9, -20(s0)
  lw   s10, -24(s0)
  lw   s11, -28(s0)
  lw   ra, 28(sp)
  lw   s0, 24(sp)
  addi sp, sp, 32
  ret

.globl show_tok
show_tok:
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
  li   t1, 11  # tag 'TNum'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s8, t2
  mv   t0, s8
  bnez t0, .show_tok_tag_ok6
  j    .show_tok_next3
.show_tok_tag_ok6:
  mv   t0, s11
  lw   t1, 4(t0)
  mv   s8, t1
  j    .show_tok_sub8
.show_tok_sub8:
  j    .show_tok_arm2
.show_tok_arm2:
  mv   t0, s11
  lw   t1, 4(t0)
  mv   s8, t1
  mv   a0, s8
  call show
  mv   s9, a0
  mv   t0, s9
  mv   s10, t0
  j    .show_tok_match_end1
.show_tok_next3:
  mv   t0, s11
  lw   t1, 0(t0)
  mv   s9, t1
  mv   t0, s9
  li   t1, 12  # tag 'TPlus'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s8, t2
  mv   t0, s8
  bnez t0, .show_tok_arm11
  j    .show_tok_next12
.show_tok_arm11:
  la   t0, .Lstr3
  mv   s10, t0
  j    .show_tok_match_end1
.show_tok_next12:
  mv   t0, s11
  lw   t1, 0(t0)
  mv   s8, t1
  mv   t0, s8
  li   t1, 10  # tag 'TMinus'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s9, t2
  mv   t0, s9
  bnez t0, .show_tok_arm15
  j    .show_tok_next16
.show_tok_arm15:
  la   t0, .Lstr5
  mv   s10, t0
  j    .show_tok_match_end1
.show_tok_next16:
  mv   t0, s11
  lw   t1, 0(t0)
  mv   s9, t1
  mv   t0, s9
  li   t1, 15  # tag 'TStar'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s8, t2
  mv   t0, s8
  bnez t0, .show_tok_arm19
  j    .show_tok_next20
.show_tok_arm19:
  la   t0, .Lstr6
  mv   s10, t0
  j    .show_tok_match_end1
.show_tok_next20:
  mv   t0, s11
  lw   t1, 0(t0)
  mv   s8, t1
  mv   t0, s8
  li   t1, 14  # tag 'TSlash'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s9, t2
  mv   t0, s9
  bnez t0, .show_tok_arm23
  j    .show_tok_next24
.show_tok_arm23:
  la   t0, .Lstr7
  mv   s10, t0
  j    .show_tok_match_end1
.show_tok_next24:
  mv   t0, s11
  lw   t1, 0(t0)
  mv   s9, t1
  mv   t0, s9
  li   t1, 9  # tag 'TLParen'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s8, t2
  mv   t0, s8
  bnez t0, .show_tok_arm27
  j    .show_tok_next28
.show_tok_arm27:
  la   t0, .Lstr2
  mv   s10, t0
  j    .show_tok_match_end1
.show_tok_next28:
  mv   t0, s11
  lw   t1, 0(t0)
  mv   s8, t1
  mv   t0, s8
  li   t1, 13  # tag 'TRParen'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s9, t2
  mv   t0, s9
  bnez t0, .show_tok_arm31
  j    .show_tok_next32
.show_tok_arm31:
  la   t0, .Lstr4
  mv   s10, t0
  j    .show_tok_match_end1
.show_tok_next32:
  call __lark_match_fail
.show_tok_match_end1:
  mv   a0, s10
  lw   s8, -12(s0)
  lw   s9, -16(s0)
  lw   s10, -20(s0)
  lw   s11, -24(s0)
  lw   ra, 28(sp)
  lw   s0, 24(sp)
  addi sp, sp, 32
  ret

.globl show_toks
show_toks:
  addi sp, sp, -32
  sw   ra, 28(sp)
  sw   s0, 24(sp)
  addi s0, sp, 32
  sw   s7, -12(s0)
  sw   s8, -16(s0)
  sw   s9, -20(s0)
  sw   s10, -24(s0)
  sw   s11, -28(s0)
  mv   s11, a0
  mv   t0, s11
  lw   t1, 0(t0)
  mv   s9, t1
  mv   t0, s9
  li   t1, 6  # tag 'Nil'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s8, t2
  mv   t0, s8
  bnez t0, .show_toks_arm2
  j    .show_toks_next3
.show_toks_arm2:
  la   t0, .Lstr8
  mv   s10, t0
  j    .show_toks_match_end1
.show_toks_next3:
  mv   t0, s11
  lw   t1, 0(t0)
  mv   s8, t1
  mv   t0, s8
  li   t1, 1  # tag 'Cons'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s9, t2
  mv   t0, s9
  bnez t0, .show_toks_tag_ok10
  j    .show_toks_next7
.show_toks_tag_ok10:
  mv   t0, s11
  lw   t1, 4(t0)
  mv   s9, t1
  j    .show_toks_sub12
.show_toks_sub12:
  mv   t0, s11
  lw   t1, 8(t0)
  mv   s9, t1
  mv   t0, s9
  lw   t1, 0(t0)
  mv   s8, t1
  mv   t0, s8
  li   t1, 6  # tag 'Nil'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s9, t2
  mv   t0, s9
  bnez t0, .show_toks_sub14
  j    .show_toks_next7
.show_toks_sub14:
  j    .show_toks_arm6
.show_toks_arm6:
  mv   t0, s11
  lw   t1, 4(t0)
  mv   s9, t1
  mv   t0, s11
  lw   t1, 8(t0)
  mv   s8, t1
  mv   a0, s9
  call show_tok
  mv   s8, a0
  mv   t0, s8
  mv   s10, t0
  j    .show_toks_match_end1
.show_toks_next7:
  mv   t0, s11
  lw   t1, 0(t0)
  mv   s8, t1
  mv   t0, s8
  li   t1, 1  # tag 'Cons'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s9, t2
  mv   t0, s9
  bnez t0, .show_toks_tag_ok24
  j    .show_toks_next21
.show_toks_tag_ok24:
  mv   t0, s11
  lw   t1, 4(t0)
  mv   s9, t1
  j    .show_toks_sub26
.show_toks_sub26:
  mv   t0, s11
  lw   t1, 8(t0)
  mv   s9, t1
  j    .show_toks_sub28
.show_toks_sub28:
  j    .show_toks_arm20
.show_toks_arm20:
  mv   t0, s11
  lw   t1, 4(t0)
  mv   s9, t1
  mv   t0, s11
  lw   t1, 8(t0)
  mv   s8, t1
  mv   a0, s9
  call show_tok
  mv   s7, a0
  mv   a0, s7
  la   a1, .Lstr9
  call __str_concat
  mv   s9, a0
  mv   a0, s8
  call show_toks
  mv   s7, a0
  mv   a0, s9
  mv   a1, s7
  call __str_concat
  mv   s8, a0
  mv   t0, s8
  mv   s10, t0
  j    .show_toks_match_end1
.show_toks_next21:
  call __lark_match_fail
.show_toks_match_end1:
  mv   a0, s10
  lw   s7, -12(s0)
  lw   s8, -16(s0)
  lw   s9, -20(s0)
  lw   s10, -24(s0)
  lw   s11, -28(s0)
  lw   ra, 28(sp)
  lw   s0, 24(sp)
  addi sp, sp, 32
  ret

.globl run
run:
  addi sp, sp, -48
  sw   ra, 44(sp)
  sw   s0, 40(sp)
  addi s0, sp, 48
  sw   s5, -12(s0)
  sw   s6, -16(s0)
  sw   s7, -20(s0)
  sw   s8, -24(s0)
  sw   s9, -28(s0)
  sw   s10, -32(s0)
  sw   s11, -36(s0)
  mv   s11, a0
  mv   a0, s11
  call show_toks
  mv   s9, a0
  mv   a0, s11
  call p_expr
  mv   s8, a0
  mv   t0, s8
  lw   t1, 0(t0)
  mv   s7, t1
  mv   t0, s7
  li   t1, 3  # tag 'Err'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s6, t2
  mv   t0, s6
  bnez t0, .run_tag_ok8
  j    .run_next5
.run_tag_ok8:
  mv   t0, s8
  lw   t1, 4(t0)
  mv   s6, t1
  j    .run_sub10
.run_sub10:
  j    .run_arm4
.run_arm4:
  mv   t0, s8
  lw   t1, 4(t0)
  mv   s6, t1
  mv   a0, s9
  la   a1, .Lstr10
  call __str_concat
  mv   s11, a0
  mv   a0, s11
  mv   a1, s6
  call __str_concat
  mv   s7, a0
  mv   t0, s7
  mv   s10, t0
  j    .run_match_end3
.run_next5:
  mv   t0, s8
  lw   t1, 0(t0)
  mv   s7, t1
  mv   t0, s7
  li   t1, 7  # tag 'Ok'
  sub  t2, t0, t1
  seqz t2, t2
  mv   s11, t2
  mv   t0, s11
  bnez t0, .run_tag_ok18
  j    .run_next15
.run_tag_ok18:
  mv   t0, s8
  lw   t1, 4(t0)
  mv   s11, t1
  mv   t0, s11
  lw   t1, 4(t0)
  mv   s7, t1
  j    .run_sub22
.run_sub22:
  mv   t0, s11
  lw   t1, 8(t0)
  mv   s7, t1
  j    .run_sub24
.run_sub24:
  j    .run_sub20
.run_sub20:
  j    .run_arm14
.run_arm14:
  mv   t0, s8
  lw   t1, 4(t0)
  mv   s11, t1
  mv   t0, s11
  lw   t1, 4(t0)
  mv   s7, t1
  mv   t0, s11
  lw   t1, 8(t0)
  mv   s6, t1
  mv   a0, s9
  la   a1, .Lstr11
  call __str_concat
  mv   s6, a0
  mv   a0, s7
  call pretty
  mv   s11, a0
  mv   a0, s6
  mv   a1, s11
  call __str_concat
  mv   s5, a0
  mv   a0, s5
  la   a1, .Lstr12
  call __str_concat
  mv   s11, a0
  mv   a0, s7
  call eval
  mv   s5, a0
  mv   a0, s5
  call show
  mv   s7, a0
  mv   a0, s11
  mv   a1, s7
  call __str_concat
  mv   s5, a0
  mv   t0, s5
  mv   s10, t0
  j    .run_match_end3
.run_next15:
  call __lark_match_fail
.run_match_end3:
  mv   a0, s10
  lw   s5, -12(s0)
  lw   s6, -16(s0)
  lw   s7, -20(s0)
  lw   s8, -24(s0)
  lw   s9, -28(s0)
  lw   s10, -32(s0)
  lw   s11, -36(s0)
  lw   ra, 44(sp)
  lw   s0, 40(sp)
  addi sp, sp, 48
  ret

.globl lark_main
lark_main:
  addi sp, sp, -80
  sw   ra, 76(sp)
  sw   s0, 72(sp)
  addi s0, sp, 80
  sw   s1, -12(s0)
  sw   s2, -16(s0)
  sw   s3, -20(s0)
  sw   s4, -24(s0)
  sw   s5, -28(s0)
  sw   s6, -32(s0)
  sw   s7, -36(s0)
  sw   s8, -40(s0)
  sw   s9, -44(s0)
  sw   s10, -48(s0)
  sw   s11, -52(s0)
  sw   a0, -56(s0)
  li   a0, 2
  call __heap_alloc
  mv   t3, a0
  li   t0, 11  # TNum
  sw   t0, 0(t3)
  li   t0, 1
  sw   t0, 4(t3)
  mv   s10, t3
  li   a0, 1
  call __heap_alloc
  mv   t3, a0
  li   t0, 12  # TPlus
  sw   t0, 0(t3)
  mv   s9, t3
  li   a0, 2
  call __heap_alloc
  mv   t3, a0
  li   t0, 11  # TNum
  sw   t0, 0(t3)
  li   t0, 2
  sw   t0, 4(t3)
  mv   s8, t3
  li   a0, 1
  call __heap_alloc
  mv   t3, a0
  li   t0, 15  # TStar
  sw   t0, 0(t3)
  mv   s7, t3
  li   a0, 2
  call __heap_alloc
  mv   t3, a0
  li   t0, 11  # TNum
  sw   t0, 0(t3)
  li   t0, 3
  sw   t0, 4(t3)
  mv   s6, t3
  li   a0, 1
  call __heap_alloc
  mv   t3, a0
  li   t0, 6  # Nil
  sw   t0, 0(t3)
  mv   s5, t3
  li   a0, 3
  call __heap_alloc
  mv   t3, a0
  li   t0, 1  # Cons
  sw   t0, 0(t3)
  mv   t0, s6
  sw   t0, 4(t3)
  mv   t0, s5
  sw   t0, 8(t3)
  mv   s4, t3
  li   a0, 3
  call __heap_alloc
  mv   t3, a0
  li   t0, 1  # Cons
  sw   t0, 0(t3)
  mv   t0, s7
  sw   t0, 4(t3)
  mv   t0, s4
  sw   t0, 8(t3)
  mv   s5, t3
  li   a0, 3
  call __heap_alloc
  mv   t3, a0
  li   t0, 1  # Cons
  sw   t0, 0(t3)
  mv   t0, s8
  sw   t0, 4(t3)
  mv   t0, s5
  sw   t0, 8(t3)
  mv   s4, t3
  li   a0, 3
  call __heap_alloc
  mv   t3, a0
  li   t0, 1  # Cons
  sw   t0, 0(t3)
  mv   t0, s9
  sw   t0, 4(t3)
  mv   t0, s4
  sw   t0, 8(t3)
  mv   s5, t3
  li   a0, 3
  call __heap_alloc
  mv   t3, a0
  li   t0, 1  # Cons
  sw   t0, 0(t3)
  mv   t0, s10
  sw   t0, 4(t3)
  mv   t0, s5
  sw   t0, 8(t3)
  sw   t3, -68(s0)
  li   a0, 1
  call __heap_alloc
  mv   t3, a0
  li   t0, 9  # TLParen
  sw   t0, 0(t3)
  mv   s5, t3
  li   a0, 2
  call __heap_alloc
  mv   t3, a0
  li   t0, 11  # TNum
  sw   t0, 0(t3)
  li   t0, 1
  sw   t0, 4(t3)
  mv   s10, t3
  li   a0, 1
  call __heap_alloc
  mv   t3, a0
  li   t0, 12  # TPlus
  sw   t0, 0(t3)
  mv   s9, t3
  li   a0, 2
  call __heap_alloc
  mv   t3, a0
  li   t0, 11  # TNum
  sw   t0, 0(t3)
  li   t0, 2
  sw   t0, 4(t3)
  mv   s8, t3
  li   a0, 1
  call __heap_alloc
  mv   t3, a0
  li   t0, 13  # TRParen
  sw   t0, 0(t3)
  mv   s7, t3
  li   a0, 1
  call __heap_alloc
  mv   t3, a0
  li   t0, 15  # TStar
  sw   t0, 0(t3)
  mv   s6, t3
  li   a0, 2
  call __heap_alloc
  mv   t3, a0
  li   t0, 11  # TNum
  sw   t0, 0(t3)
  li   t0, 3
  sw   t0, 4(t3)
  mv   s3, t3
  li   a0, 1
  call __heap_alloc
  mv   t3, a0
  li   t0, 6  # Nil
  sw   t0, 0(t3)
  mv   s2, t3
  li   a0, 3
  call __heap_alloc
  mv   t3, a0
  li   t0, 1  # Cons
  sw   t0, 0(t3)
  mv   t0, s3
  sw   t0, 4(t3)
  mv   t0, s2
  sw   t0, 8(t3)
  mv   s1, t3
  li   a0, 3
  call __heap_alloc
  mv   t3, a0
  li   t0, 1  # Cons
  sw   t0, 0(t3)
  mv   t0, s6
  sw   t0, 4(t3)
  mv   t0, s1
  sw   t0, 8(t3)
  mv   s2, t3
  li   a0, 3
  call __heap_alloc
  mv   t3, a0
  li   t0, 1  # Cons
  sw   t0, 0(t3)
  mv   t0, s7
  sw   t0, 4(t3)
  mv   t0, s2
  sw   t0, 8(t3)
  mv   s1, t3
  li   a0, 3
  call __heap_alloc
  mv   t3, a0
  li   t0, 1  # Cons
  sw   t0, 0(t3)
  mv   t0, s8
  sw   t0, 4(t3)
  mv   t0, s1
  sw   t0, 8(t3)
  mv   s2, t3
  li   a0, 3
  call __heap_alloc
  mv   t3, a0
  li   t0, 1  # Cons
  sw   t0, 0(t3)
  mv   t0, s9
  sw   t0, 4(t3)
  mv   t0, s2
  sw   t0, 8(t3)
  mv   s1, t3
  li   a0, 3
  call __heap_alloc
  mv   t3, a0
  li   t0, 1  # Cons
  sw   t0, 0(t3)
  mv   t0, s10
  sw   t0, 4(t3)
  mv   t0, s1
  sw   t0, 8(t3)
  mv   s2, t3
  li   a0, 3
  call __heap_alloc
  mv   t3, a0
  li   t0, 1  # Cons
  sw   t0, 0(t3)
  mv   t0, s5
  sw   t0, 4(t3)
  mv   t0, s2
  sw   t0, 8(t3)
  sw   t3, -64(s0)
  li   a0, 2
  call __heap_alloc
  mv   t3, a0
  li   t0, 11  # TNum
  sw   t0, 0(t3)
  li   t0, 10
  sw   t0, 4(t3)
  mv   s2, t3
  li   a0, 1
  call __heap_alloc
  mv   t3, a0
  li   t0, 10  # TMinus
  sw   t0, 0(t3)
  mv   s5, t3
  li   a0, 2
  call __heap_alloc
  mv   t3, a0
  li   t0, 11  # TNum
  sw   t0, 0(t3)
  li   t0, 3
  sw   t0, 4(t3)
  mv   s10, t3
  li   a0, 1
  call __heap_alloc
  mv   t3, a0
  li   t0, 10  # TMinus
  sw   t0, 0(t3)
  mv   s9, t3
  li   a0, 2
  call __heap_alloc
  mv   t3, a0
  li   t0, 11  # TNum
  sw   t0, 0(t3)
  li   t0, 2
  sw   t0, 4(t3)
  mv   s8, t3
  li   a0, 1
  call __heap_alloc
  mv   t3, a0
  li   t0, 6  # Nil
  sw   t0, 0(t3)
  mv   s7, t3
  li   a0, 3
  call __heap_alloc
  mv   t3, a0
  li   t0, 1  # Cons
  sw   t0, 0(t3)
  mv   t0, s8
  sw   t0, 4(t3)
  mv   t0, s7
  sw   t0, 8(t3)
  mv   s6, t3
  li   a0, 3
  call __heap_alloc
  mv   t3, a0
  li   t0, 1  # Cons
  sw   t0, 0(t3)
  mv   t0, s9
  sw   t0, 4(t3)
  mv   t0, s6
  sw   t0, 8(t3)
  mv   s7, t3
  li   a0, 3
  call __heap_alloc
  mv   t3, a0
  li   t0, 1  # Cons
  sw   t0, 0(t3)
  mv   t0, s10
  sw   t0, 4(t3)
  mv   t0, s7
  sw   t0, 8(t3)
  mv   s6, t3
  li   a0, 3
  call __heap_alloc
  mv   t3, a0
  li   t0, 1  # Cons
  sw   t0, 0(t3)
  mv   t0, s5
  sw   t0, 4(t3)
  mv   t0, s6
  sw   t0, 8(t3)
  mv   s7, t3
  li   a0, 3
  call __heap_alloc
  mv   t3, a0
  li   t0, 1  # Cons
  sw   t0, 0(t3)
  mv   t0, s2
  sw   t0, 4(t3)
  mv   t0, s7
  sw   t0, 8(t3)
  sw   t3, -60(s0)
  li   a0, 2
  call __heap_alloc
  mv   t3, a0
  li   t0, 11  # TNum
  sw   t0, 0(t3)
  li   t0, 2
  sw   t0, 4(t3)
  mv   s7, t3
  li   a0, 1
  call __heap_alloc
  mv   t3, a0
  li   t0, 15  # TStar
  sw   t0, 0(t3)
  mv   s2, t3
  li   a0, 1
  call __heap_alloc
  mv   t3, a0
  li   t0, 9  # TLParen
  sw   t0, 0(t3)
  mv   s5, t3
  li   a0, 2
  call __heap_alloc
  mv   t3, a0
  li   t0, 11  # TNum
  sw   t0, 0(t3)
  li   t0, 3
  sw   t0, 4(t3)
  mv   s10, t3
  li   a0, 1
  call __heap_alloc
  mv   t3, a0
  li   t0, 12  # TPlus
  sw   t0, 0(t3)
  mv   s9, t3
  li   a0, 2
  call __heap_alloc
  mv   t3, a0
  li   t0, 11  # TNum
  sw   t0, 0(t3)
  li   t0, 4
  sw   t0, 4(t3)
  mv   s8, t3
  li   a0, 1
  call __heap_alloc
  mv   t3, a0
  li   t0, 13  # TRParen
  sw   t0, 0(t3)
  mv   s3, t3
  li   a0, 1
  call __heap_alloc
  mv   t3, a0
  li   t0, 14  # TSlash
  sw   t0, 0(t3)
  mv   s11, t3
  li   a0, 2
  call __heap_alloc
  mv   t3, a0
  li   t0, 11  # TNum
  sw   t0, 0(t3)
  li   t0, 7
  sw   t0, 4(t3)
  mv   s6, t3
  li   a0, 1
  call __heap_alloc
  mv   t3, a0
  li   t0, 6  # Nil
  sw   t0, 0(t3)
  mv   s1, t3
  li   a0, 3
  call __heap_alloc
  mv   t3, a0
  li   t0, 1  # Cons
  sw   t0, 0(t3)
  mv   t0, s6
  sw   t0, 4(t3)
  mv   t0, s1
  sw   t0, 8(t3)
  mv   s4, t3
  li   a0, 3
  call __heap_alloc
  mv   t3, a0
  li   t0, 1  # Cons
  sw   t0, 0(t3)
  mv   t0, s11
  sw   t0, 4(t3)
  mv   t0, s4
  sw   t0, 8(t3)
  mv   s1, t3
  li   a0, 3
  call __heap_alloc
  mv   t3, a0
  li   t0, 1  # Cons
  sw   t0, 0(t3)
  mv   t0, s3
  sw   t0, 4(t3)
  mv   t0, s1
  sw   t0, 8(t3)
  mv   s4, t3
  li   a0, 3
  call __heap_alloc
  mv   t3, a0
  li   t0, 1  # Cons
  sw   t0, 0(t3)
  mv   t0, s8
  sw   t0, 4(t3)
  mv   t0, s4
  sw   t0, 8(t3)
  mv   s1, t3
  li   a0, 3
  call __heap_alloc
  mv   t3, a0
  li   t0, 1  # Cons
  sw   t0, 0(t3)
  mv   t0, s9
  sw   t0, 4(t3)
  mv   t0, s1
  sw   t0, 8(t3)
  mv   s4, t3
  li   a0, 3
  call __heap_alloc
  mv   t3, a0
  li   t0, 1  # Cons
  sw   t0, 0(t3)
  mv   t0, s10
  sw   t0, 4(t3)
  mv   t0, s4
  sw   t0, 8(t3)
  mv   s1, t3
  li   a0, 3
  call __heap_alloc
  mv   t3, a0
  li   t0, 1  # Cons
  sw   t0, 0(t3)
  mv   t0, s5
  sw   t0, 4(t3)
  mv   t0, s1
  sw   t0, 8(t3)
  mv   s4, t3
  li   a0, 3
  call __heap_alloc
  mv   t3, a0
  li   t0, 1  # Cons
  sw   t0, 0(t3)
  mv   t0, s2
  sw   t0, 4(t3)
  mv   t0, s4
  sw   t0, 8(t3)
  mv   s1, t3
  li   a0, 3
  call __heap_alloc
  mv   t3, a0
  li   t0, 1  # Cons
  sw   t0, 0(t3)
  mv   t0, s7
  sw   t0, 4(t3)
  mv   t0, s1
  sw   t0, 8(t3)
  mv   s4, t3
  li   a0, 1
  call __heap_alloc
  mv   t3, a0
  li   t0, 9  # TLParen
  sw   t0, 0(t3)
  mv   s1, t3
  li   a0, 2
  call __heap_alloc
  mv   t3, a0
  li   t0, 11  # TNum
  sw   t0, 0(t3)
  li   t0, 1
  sw   t0, 4(t3)
  mv   s7, t3
  li   a0, 1
  call __heap_alloc
  mv   t3, a0
  li   t0, 12  # TPlus
  sw   t0, 0(t3)
  mv   s2, t3
  li   a0, 1
  call __heap_alloc
  mv   t3, a0
  li   t0, 6  # Nil
  sw   t0, 0(t3)
  mv   s5, t3
  li   a0, 3
  call __heap_alloc
  mv   t3, a0
  li   t0, 1  # Cons
  sw   t0, 0(t3)
  mv   t0, s2
  sw   t0, 4(t3)
  mv   t0, s5
  sw   t0, 8(t3)
  mv   s10, t3
  li   a0, 3
  call __heap_alloc
  mv   t3, a0
  li   t0, 1  # Cons
  sw   t0, 0(t3)
  mv   t0, s7
  sw   t0, 4(t3)
  mv   t0, s10
  sw   t0, 8(t3)
  mv   s5, t3
  li   a0, 3
  call __heap_alloc
  mv   t3, a0
  li   t0, 1  # Cons
  sw   t0, 0(t3)
  mv   t0, s1
  sw   t0, 4(t3)
  mv   t0, s5
  sw   t0, 8(t3)
  mv   s10, t3
  lw   a0, -68(s0)
  call run
  mv   s5, a0
  lw   a0, -56(s0)
  mv   a1, s5
  call print
  mv   s1, a0
  lw   a0, -64(s0)
  call run
  mv   s5, a0
  mv   a0, s1
  mv   a1, s5
  call print
  mv   s7, a0
  lw   a0, -60(s0)
  call run
  mv   s5, a0
  mv   a0, s7
  mv   a1, s5
  call print
  mv   s1, a0
  mv   a0, s4
  call run
  mv   s5, a0
  mv   a0, s1
  mv   a1, s5
  call print
  mv   s4, a0
  mv   a0, s10
  call run
  mv   s5, a0
  mv   a0, s4
  mv   a1, s5
  call print
  mv   s10, a0
  mv   a0, s10
  lw   s1, -12(s0)
  lw   s2, -16(s0)
  lw   s3, -20(s0)
  lw   s4, -24(s0)
  lw   s5, -28(s0)
  lw   s6, -32(s0)
  lw   s7, -36(s0)
  lw   s8, -40(s0)
  lw   s9, -44(s0)
  lw   s10, -48(s0)
  lw   s11, -52(s0)
  lw   ra, 76(sp)
  lw   s0, 72(sp)
  addi sp, sp, 80
  ret
