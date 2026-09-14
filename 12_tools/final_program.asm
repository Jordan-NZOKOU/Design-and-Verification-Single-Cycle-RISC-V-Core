# Full demonstration program for the implemented RV32I subset.
addi x5,  x0, 5
addi x6,  x0, 4
or   x7,  x5, x6
and  x8,  x5, x6
sub  x9,  x5, x6
slt  x10, x6, x5
sw   x7,  0(x0)
lw   x11, 0(x0)
beq  x11, x7, equal
addi x12, x0, 99      # Must be skipped by the taken branch.
equal:
add  x12, x9, x10
sw   x12, 4(x0)
addi x13, x0, -1
slt  x14, x13, x0
or   x15, x13, x0
done:
beq  x0, x0, done
