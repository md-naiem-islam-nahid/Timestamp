section .data
    msg db 'Hello, World!', 0Ah
section .text
    global _start
_start:
    mov edx, 13
    mov ecx, msg
    mov ebx, 1
    mov eax, 4
    int 80h
    mov eax, 1
    int 80h

===========================================
Created by: MD. Naiem Islam Nahid
File Type: Assembly (NASM)
Magic Number: 2155
Time: 2024-11-07T05:02:51.551895
Date: Thursday, 07 November 2024, 2024th century
Emoji: None
===========================================
