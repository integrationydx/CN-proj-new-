# Distributed Reservation System with SQLite Persistence

## Overview

This project implements a **TCP-based distributed reservation system** that handles multiple client booking requests simultaneously while preventing **double booking of shared resources** and persisting state in **SQLite**.

The system follows a **client-server architecture** where multiple clients connect to a reservation server through a custom request-response protocol. The server manages seat reservations and ensures **data consistency using concurrency control mechanisms**.

The project demonstrates important concepts from **Computer Networks and Distributed Systems**, including socket communication, concurrency handling, resource synchronization, and database-backed persistence.

---

# Features

### 1. TCP Client-Server Architecture

* Clients communicate with the server using **TCP sockets**
* Reliable communication ensures that booking requests are delivered correctly

### 2. Concurrency Control

* Multiple clients can send booking requests simultaneously
* The server uses **seat-level locking** to prevent race conditions

### 3. Prevention of Double Booking

* A seat can only be booked by **one client at a time**
* Locking ensures that two clients cannot reserve the same seat concurrently

### 4. Seat Locking Mechanism

* Clients must **lock a seat before booking**
* Prevents other clients from accessing the seat during the booking process

### 5. Waitlist System

* If a seat is already booked, additional users are added to a **waitlist queue**
* When the seat becomes available, it is automatically assigned to the next client in the waitlist

### 6. Seat Map Visualization

Clients can view the current seat status:

```
[ ] → Available seat
[X] → Booked seat
```

### 7. Persistent Storage

Seat and user data are stored in a **SQLite database** (`reservation.db`).

This allows the system to:

* Maintain booking information
* Recover seat and user state even after server restart
* Safely handle multiple client requests against the same database

### 8. Write-Ahead Logging (WAL)

The server can be extended with transaction logging or WAL mode.

### 9. Multi-User Session Simulation

The client application allows users to **login and logout as different clients** within the same terminal.

Example:

```
Login: C1
C1> book 3
C1> logout
Login: C2
```

This simplifies testing without running multiple terminals.

---

# System Architecture

The system follows a **Client-Server Topology**.

```
        Client C1
           |
        Client C2
           |
        Client C3
           |
        TCP Network
           |
     -----------------
     | Reservation   |
     |    Server     |
     -----------------
           |
     SQLite Database
```

### Components

**Client**

* Sends booking requests
* Displays seat status

**Server**

* Handles client requests
* Controls seat access
* Maintains booking data in SQLite

---

# Technologies Used

| Technology   | Purpose                           |
| ------------ | --------------------------------- |
| Python       | Implementation language           |
| TCP Sockets  | Network communication             |
| SSL/TLS      | Secure communication              |
| Threading    | Handling multiple client requests |
| SQLite       | Persistent storage of users and seats |
| Git & GitHub | Version control                   |

---

# Custom Protocol

The system uses a **custom text-based request-response protocol** over SSL.

### Client Commands

```
login <username> <password>
lock <seat_number>
book <seat_number>
cancel <seat_number>
map
status
mybookings
logout
```

### Example Session

```
Login as client: C1

C1> map
A1: free
A2: free

C1> lock 3
3 locked

C1> book 3
3 booked

C1> mybookings
['3']
```

---

# Installation and Setup

## 1. Clone the Repository

```
git clone https://github.com/YOURUSERNAME/distributed-reservation-system.git
```

```
cd distributed-reservation-system
```

---

## 2. Create TLS Certificates

The server expects `cert.pem` and `key.pem` in the project folder.

Example using OpenSSL:

```bash
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes
```

## 3. Run the Server

```
python server.py
```

The server will start listening for client connections.

```
Reservation Server Running
```

## 4. Run the Client

Open a new terminal and run:

```
python client.py
```

You will see:

```
Reservation System
Login as client (ex: C1, C2)
```

---

# Testing the System

Example test scenario:

### Client 1

```
Login: C1
lock 5
book 5
logout
```

### Client 2

```
Login: C2
lock 5
```

Output:

```
SEAT BOOKED
```

This demonstrates that **double booking is prevented**.

---

# Concurrency Handling

The system uses **database transactions** and a small in-process lock around write operations.

This reduces the chance of race conditions when multiple clients try to book the same seat.
