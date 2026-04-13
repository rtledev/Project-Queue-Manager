// OfficeHoursList renders the left column of the homepage.
// It receives office-hours data, loading/error state, and a click handler
// for the Join Queue button on each office-hours card.
export default function OfficeHoursList({
    officeHours,
    loading,
    error,
    onJoinQueue,
}) {
    return (
        /* Left column: available office hours cards */
        <div className="rounded-3xl bg-white p-6 shadow-sm">
            <div className="mb-5 flex items-center justify-between">
                <div>
                    <h3 className="text-xl font-semibold text-slate-900">Available Office Hours</h3>
                    <p className="mt-1 text-sm text-slate-500">Browse open sessions and join the queue.</p>
                </div>

                <button className="rounded-2xl border border-slate-200 px-4 py-2 text-sm text-slate-600 hover:bg-slate-50">
                    View All
                </button>
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
                            <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">

                                {/* Left side of the card: icon + basic information */}
                                <div className="flex items-center gap-4">
                                    <div className="flex h-14 w-14 items-center justify-center rounded-full bg-slate-200 text-xl">
                                        👤
                                    </div>

                                    <div>
                                        <h4 className="text-lg font-semibold text-slate-900">{person.name}</h4>
                                        <p className="text-sm text-slate-500">
                                            {person.role} • {person.subtitle}
                                        </p>
                                    </div>
                                </div>

                                {/* Right side of the card: status + queue count + action */}
                                <div className="flex flex-wrap items-center gap-3">
                                    <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
                                        {person.status}
                                    </span>

                                    <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
                                        {person.studentsWaiting} waiting
                                    </span>

                                    <button
                                        onClick={() => onJoinQueue(person)}
                                        className="rounded-2xl bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
                                    >
                                        Join Queue
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