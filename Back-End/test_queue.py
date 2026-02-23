from Priority_Queue import MeetingQueueManager, MeetingRequest, NotFoundError

# Helper function to print the merged queue in a readable format
def print_merged(qm: MeetingQueueManager, label: str): # Added label parameter to clarify the context of the merged queue being printed
    print(f"\n ---{label}--- ")
    merged = qm.merged_queue()
    for i, req in enumerate(merged, start=1):
        tier = "DSL" if req.is_dsl_queue else "Non-DSL"
        print(f"{i:>2}. {req.student_name:10} | {req.student_id} | {tier} | {req.title} | status={req.status}")

# This test checks that when both DSL and non-DSL requests are enqueued, the merged view correctly prioritizes DSL requests while maintaining FCFS order within each tier. It also validates that the positions of each request in the merged queue are as expected.
def test_01_DSL_first():
    print("\n [TEST 01] DSL-first ordering + FCFS within tiers")
    qm = MeetingQueueManager()

    # Create request objects for enque()
    req = MeetingRequest("S1", "Alice", "alice@gmail.com", "Threads help", is_dsl_queue=False)
    req2 = MeetingRequest("S2", "Bob", "bob@gmail.com", "Matrix help", is_dsl_queue=True)
    req3 = MeetingRequest("S3", "Charlie", "char@gmail.com", "Recursion help", is_dsl_queue=False)
    req4 = MeetingRequest("S4", "Diana", "diana@gmail.com", "Algorithms help", is_dsl_queue=True)

    # Non-DSL joins first
    qm.enqueue(req)
    # DSL joins second (Should jump ahead in merged views)
    qm.enqueue(req2)
    # Non-DSL joins third
    qm.enqueue(req3)
    # DSL joins fourth (should be behind bob but ahead of non-dsl)
    qm.enqueue(req4)

    # Print merged view to visually confirm order
    print_merged(qm, "Merged Queue should be: Bob (DSL), Diana (DSL), Alice (Non-DSL), Charlie (Non-DSL)")

    # Assertions to validate the order in the merged queue and positions
    assert [r.student_id for r in qm.merged_queue()] == ["S2", "S4", "S1", "S3"]
    assert qm.get_position("S2") == 1
    assert qm.get_position("S4") == 2
    assert qm.get_position("S1") == 3
    assert qm.get_position("S3") == 4
    print("Test 01 passed!")

# This test checks that the peek and dequeue operations correctly prioritize DSL requests over non-DSL requests, and that the status of dequeued requests is updated to "completed". 
# It also confirms that after serving a DSL request, the next request in the merged queue is the correct one.
def test_02_peek_and_dequeue():
    print("\n [TEST 02] Peek and Dequeue functionality")
    qm = MeetingQueueManager()

    # Create request objects for enque()
    req = MeetingRequest("S1", "Alice", "alice@gmail.com", "Threads help", is_dsl_queue=False)
    req2 = MeetingRequest("S2", "Bob", "bob@gmail.com", "Matrix help", is_dsl_queue=True)

    # Enqueue both requests
    qm.enqueue(req)
    qm.enqueue(req2)

    # Peek should show Bob (DSL) as next, even though Alice (Non-DSL) arrived first
    nxt= qm.peek_next()
    print("Peeked Request:", nxt.student_name if nxt else None)
    assert nxt is not None and nxt.student_id == "S2", "Peek should return the DSL request (Bob)"

    # Dequeue should also return Bob and mark him as Served
    completed = qm.dequeue_next()
    print("Dequeued Request:", completed.student_name if completed else None)
    assert completed is not None and completed.student_id == "S2", "Dequeue should return the DSL request (Bob)"
    assert completed.status == "Completed", "Dequeued request should be marked as Served"

    # After serving Bob, the merged queue should only contain Alice (Non-DSL)
    print_merged(qm, "After serving Bob, queue should contain only Alice (Non-DSL)")
    assert [r.student_id for r in qm.merged_queue()] == ["S1"]
    print("Test 02 passed!")

# This test checks that cancelling a request properly removes it from the queue and updates the merged view accordingly. 
# It also checks that trying to cancel a non-existent request returns False.
def test_03_cancel_request():
    print("\n [TEST 03] Cancel Request functionality")
    qm = MeetingQueueManager()
    
    # Create request objects for enque()
    req = MeetingRequest("S1", "Alice", "alice@gmail.com", "Threads help", is_dsl_queue=False)
    req2 = MeetingRequest("S2", "Bob", "bob@gmail.com", "Matrix help", is_dsl_queue=True)
    req3 = MeetingRequest("S3", "Charlie", "char@gmail.com", "Recursion help", is_dsl_queue=False)

    # Enqueue requests
    qm.enqueue(req)
    qm.enqueue(req2)
    qm.enqueue(req3)
    
    # Initial merged view should show Bob (DSL) first, then Alice and Charlie (Non-DSL)
    print_merged(qm, "Initial Queue: Bob (DSL), Alice (Non-DSL), Charlie (Non-DSL)")

    # Cancel Bob's request
    ok = qm.cancel_by_student("S2")
    print("Cancel Bob's Request:", ok)
    assert ok is True
    print_merged(qm, "After cancelling Bob: Alice (Non-DSL), Charlie (Non-DSL)")
    assert [r.student_id for r in qm.merged_queue()] == ["S1", "S3"]
    
    # Try cancelling a non-existent request
    ok = qm.cancel_by_student("S999")
    print("Cancel non-existent request S999:", ok)
    assert ok is False

    print("Test 03 passed!")

# This test checks that the system prevents a student from having multiple active requests in the queue. It attempts to enqueue two requests from the same student and expects an exception to be raised for the second request.
def test_04_duplicate_active_request():
    print("\n [TEST 04] Preventing duplicate active requests from the same student")
    qm = MeetingQueueManager()

    req = MeetingRequest("S1", "Alice", "alice@gmail.com", "Threads help", is_dsl_queue=False)
    
    # Student S1 submits a request
    qm.enqueue(req)
    
    # Try to submit another request from the same student
    try:
        qm.enqueue(req)
        # If we reach this point, it means the duplicate request was allowed, which is a failure
        raise AssertionError("Should have raised an exception for duplicate active request")
    except Exception as e:
        print("Caught exception (Expected):", type(e).__name__)
        print("Test 04 passed!")

# This test checks that if a student is not currently in the queue, their position should be None
def test_05_position_none_when_not_waiting(): 
    print("\n [TEST 05] Position should be None when student is not waiting")
    qm = MeetingQueueManager()

    # Create request objects for enque()
    req = MeetingRequest("S1", "Alice", "alice@gmail.com", "Threads help", is_dsl_queue=False)
    
    # Student S1 submits a request
    qm.enqueue(req)
    assert qm.get_position("S1") == 1, "S1 should be at position 1"
    
    qm.dequeue_next()  # Serve S1, now S1 should not be in the queue
    assert qm.get_position("S1") is None, "S1 should not have a position after being served"
    print("Test 05 passed!")

if __name__ == "__main__":
    test_01_DSL_first()
    test_02_peek_and_dequeue()
    test_03_cancel_request()
    test_04_duplicate_active_request()
    test_05_position_none_when_not_waiting()

    print("\nAll tests completed successfully!")

    
