// OfficeHoursList renders the left column of the homepage.
// It receives office-hours data, loading/error state, the current signed-in student,
// current queue status, and the click handler for the Join Queue button.
export default function OfficeHoursList({
    officeHours,
    loading,
    error,
    onJoinQueue,
    currentStudent,
    queueStatus,
}) {
    /*
      isStudentInQueue is true when the signed-in student currently has
      an active queue request.

      Right now, the prototype uses one shared queue, so this flag is enough
      to decide whether the Join Queue button should be disabled.
    */
    const isStudentInQueue = Boolean(currentStudent && queueStatus);

    return (
        /* Left column: available office hours cards */
        <div className="rounded-3xl bg-white p-6 shadow-sm">
            <div className="mb-5 flex items-center justify-between">
                <div>
                    <h3 className="text-xl font-semibold text-slate-900">Available Office Hours</h3>
                    <p className="mt-1 text-sm text-slate-500">
                        Browse open sessions, review details, and join the queue.
                    </p>
                </div>
            </div>

            {/* Show loading message while office-hours data is being fetched */}
            {loading && (
                <p className="text-sm text-slate-500">Loading office hours...</p>
            )}

            {/* Show API error if the office-hours request fails */}
            {error && (
                <p className="text-sm text-red-600">{error}</p>
            )}

            {/* Show office-hours cards once data has loaded successfully */}
            {!loading && !error && (
                <div className="space-y-4">
                    {officeHours.map((person) => (
                        <div
                            key={person.id}
                            className="rounded-3xl border border-slate-200 p-5 transition hover:shadow-md"
                        >
                            <div className="flex flex-col gap-4">
                                {/* Top row: icon, staff details, and badges */}
                                <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                                    <div className="flex items-center gap-4">
                                        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-slate-200 text-xl">
                                            👤
                                        </div>

                                        <div>
                                            <h4 className="text-lg font-semibold text-slate-900">
                                                {person.name}
                                            </h4>
                                            <p className="text-sm text-slate-500">
                                                {person.role} • {person.subtitle}
                                            </p>
                                        </div>
                                    </div>

                                    <div className="flex flex-wrap items-center gap-3">
                                        <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
                                            {person.status}
                                        </span>

                                        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
                                            {person.studentsWaiting} waiting
                                        </span>

                                        {isStudentInQueue && (
                                            <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700">
                                                You are currently in queue
                                            </span>
                                        )}
                                    </div>
                                </div>

                                {/* Middle row: session details */}
                                <div className="grid gap-3 text-sm text-slate-600 md:grid-cols-2">
                                    <p>
                                        <span className="font-medium text-slate-900">Time:</span>{" "}
                                        {person.time || "Time not listed"}
                                    </p>

                                    <p>
                                        <span className="font-medium text-slate-900">Location:</span>{" "}
                                        {person.location || "Location not listed"}
                                    </p>

                                    <p>
                                        <span className="font-medium text-slate-900">Meeting Type:</span>{" "}
                                        {person.meetingType || "General help"}
                                    </p>

                                    <p>
                                        <span className="font-medium text-slate-900">Details:</span>{" "}
                                        {person.description || "No additional details available."}
                                    </p>
                                </div>

                                {/* Bottom row: action area */}
                                <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                                    <p className="text-sm text-slate-500">
                                        {isStudentInQueue
                                            ? "You already have an active queue request."
                                            : "Join this session to be added to the current queue."}
                                    </p>

                                    <button
                                        onClick={() => onJoinQueue(person)}
                                        disabled={isStudentInQueue}
                                        className={`rounded-2xl px-4 py-2 text-sm font-medium text-white ${isStudentInQueue
                                                ? "cursor-not-allowed bg-slate-400"
                                                : "bg-blue-600 hover:bg-blue-700"
                                            }`}
                                    >
                                        {isStudentInQueue ? "Already in Queue" : "Join Queue"}
                                    </button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}