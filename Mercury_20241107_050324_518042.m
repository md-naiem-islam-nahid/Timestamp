:- module hello.
:- interface.
:- import_module io.
:- pred main(io::di, io::uo) is det.
:- implementation.
main(!IO) :-
    io.write_string("Hello, World!\n", !IO).

===========================================
Created by: MD. Naiem Islam Nahid
File Type: Mercury
Magic Number: 5452
Time: 2024-11-07T05:03:24.518042
Date: Thursday, 07 November 2024, 2024th century
Emoji: None
===========================================
