// QueueStatusCard renders the student's live queue information.
// It receives the current queue status object, any queue-status-specific error,
// and the handler used to cancel the active queue request.
export default function QueueStatusCard({
    queueStatus,
    statusError,
    onCancelQueue,
}) {
    return (
        /*
          Queue status card.
          This shows the currently tracked student's queue information.

          Because queue status is re-fetched when the page first loads,
          this card can persist across browser refreshes as long as the backend
          server still has that student in the queue.
        */
        <section className="rounded-3xl bg-white p-6 shadow-sm">
            <h3 className="text-xl font-semibold text-slate-900">Your Queue Status</h3>

            <div className="mt-4 space-y-3 text-sm text-slate-600">
                {!queueStatus && !statusError && (
                    <p>You are not currently tracking an active queue request.</p>
                )}

                {statusError && (
                    <p className="text-red-600">{statusError}</p>
                )}

                {queueStatus && (
                    <>
                        <p>
                            <span className="font-medium text-slate-900">Student ID:</span>{" "}
                            {queueStatus.student_id}
                        </p>
                        <p>
                            <span className="font-medium text-slate-900">Current Position:</span>{" "}
                            {queueStatus.position}
                        </p>
                        <p>
                            <span className="font-medium text-slate-900">Status:</span>{" "}
                            Waiting
                        </p>

                        {/*
                          Cancel button for the student's active queue request.
                          This is only shown when the student is currently waiting in the queue.
                        */}
                        <div className="pt-2">
                            <button
                                onClick={onCancelQueue}
                                className="rounded-2xl border border-red-200 px-4 py-2 text-sm font-medium text-red-600 hover:bg-red-50"
                            >
                                Cancel Queue Request
                            </button>
                        </div>
                    </>
                )}
            </div>
        </section>
    );
}