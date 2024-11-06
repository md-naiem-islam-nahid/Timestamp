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
Magic Number: 8497
Time: 2024-11-07T05:04:07.369186
Date: Thursday, 07 November 2024, 2024th century
Emoji: None
===========================================
