include "console.iol"
interface HelloInterface {
    RequestResponse: hello()
}
service HelloService {
    Interfaces: HelloInterface
    Location: "socket://localhost:8000"
    hello() {
        println@Console("Hello, World!")()
    }
}

===========================================
Created by: MD. Naiem Islam Nahid
File Type: Jolie
Magic Number: 3676
Time: 2024-11-07T05:04:25.870940
Date: Thursday, 07 November 2024, 2024th century
Emoji: None
===========================================
