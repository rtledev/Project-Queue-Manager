import { useEffect, useState } from "react";

export default function DashboardPage({ onBack, currentStudent }) {
    /*
      counts stores queue totals returned by the backend.
      queue stores the merged list of all currently waiting students.
      nextStudent stores the student who would be served next.
      message stores success or error feedback for dashboard actions.
      loading tracks whether the dashboard is currently fetching backend data.
    */
    const [counts, setCounts] = useState(null);
    const [queue, setQueue] = useState([]);
    const [nextStudent, setNextStudent] = useState(null);
    const [message, setMessage] = useState("");
    const [loading, setLoading] = useState(true);
    const [sessionForm, setSessionForm] = useState({
        name: "",
        hostRole: "Professor",
        subtitle: "Office Hours",
        time: "",
        location: "",
        meetingType: "",
        description: "",
    });

    async function handleCreateSession(event) {
        event.preventDefault();

        try {
            setMessage("");

            const response = await fetch("http://127.0.0.1:5000/api/dashboard/create-office-hours", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    ...sessionForm,
                    role: currentStudent?.role || "",
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Unable to create office hours session.");
            }

            setMessage("Office hours session created successfully.");

            setSessionForm({
                name: "",
                hostRole: "Professor",
                subtitle: "Office Hours",
                time: "",
                location: "",
                meetingType: "",
                description: "",
            });

            await loadDashboardData();
        } catch (err) {
            setMessage(err.message || "Something went wrong while creating the session.");
        }
    }


    /*
      If the current signed-in account is not a professor,
      this page should not display the dashboard contents.

      This is a frontend safety check so students do not see staff-only queue data.
      The backend should also enforce professor-only access separately.
    */
    if (currentStudent?.role !== "professor") {
        return (
            <div className="min-h-screen bg-slate-100 p-6 text-slate-800">
                <div className="mx-auto max-w-3xl rounded-3xl bg-white p-8 shadow-sm">
                    <h2 className="text-2xl font-bold text-slate-900">Access Restricted</h2>
                    <p className="mt-3 text-sm text-slate-600">
                        Only professor or TA accounts can view the dashboard.
                    </p>
                    <button
                        onClick={onBack}
                        className="mt-6 rounded-2xl border border-slate-200 px-5 py-3 text-sm font-medium text-slate-700 hover:bg-slate-50"
                    >
                        Return Home
                    </button>
                </div>
            </div>
        );
    }

    /*
      loadDashboardData fetches all dashboard data from the backend:
      - queue counts
      - merged queue
      - next student

      The current signed-in account role is sent with each request so the backend
      can verify that only professor accounts are allowed to access dashboard data.
    */
    async function loadDashboardData() {
        try {
            setLoading(true);
            setMessage("");

            const requestBody = JSON.stringify({
                role: currentStudent?.role || "",
            });

            const [countsResponse, queueResponse, nextResponse] = await Promise.all([
                fetch("http://127.0.0.1:5000/api/dashboard/queue-counts", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: requestBody,
                }),
                fetch("http://127.0.0.1:5000/api/dashboard/queue", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: requestBody,
                }),
                fetch("http://127.0.0.1:5000/api/dashboard/next-student", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: requestBody,
                }),
            ]);

            const countsData = await countsResponse.json();
            const queueData = await queueResponse.json();

            let nextData = null;
            if (nextResponse.ok) {
                nextData = await nextResponse.json();
            } else {
                nextData = null;
            }

            /*
              If either the counts request or queue request fails,
              show the backend error message if available.
            */
            if (!countsResponse.ok) {
                throw new Error(countsData.error || "Failed to load queue counts.");
            }

            if (!queueResponse.ok) {
                throw new Error(queueData.error || "Failed to load queue data.");
            }

            setCounts(countsData);
            setQueue(queueData);
            setNextStudent(nextData);
        } catch (err) {
            setMessage(err.message || "Failed to load dashboard data.");
        } finally {
            setLoading(false);
        }
    }

    /*
      Run once when the dashboard first loads.
    */
    useEffect(() => {
        loadDashboardData();
    }, []);

    /*
      handleServeNext calls the backend to serve the next student.
      After serving, it reloads the dashboard so all displayed data stays in sync.

      The current signed-in account role is included so the backend can
      confirm that this action is being performed by a professor account.
    */
    async function handleServeNext() {
        try {
            setMessage("");

            const response = await fetch("http://127.0.0.1:5000/api/dashboard/serve-next", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    role: currentStudent?.role || "",
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Unable to serve next student.");
            }

            setMessage(`Now serving ${data.student_name}.`);
            await loadDashboardData();
        } catch (err) {
            setMessage(err.message || "Something went wrong while serving the next student.");
        }
    }

    return (
        <div className="min-h-screen bg-slate-100 text-slate-800">
            <div className="mx-auto flex min-h-screen max-w-7xl">
                <aside className="hidden w-64 flex-col border-r border-slate-200 bg-white lg:flex">
                    <div className="border-b border-slate-200 px-8 py-8">
                        <h1 className="text-3xl font-bold tracking-tight text-slate-900">PsNQs</h1>
                        <p className="mt-2 text-sm text-slate-500">Meeting Queue Manager</p>
                    </div>

                    <nav className="flex-1 px-4 py-6">
                        <div className="space-y-2">
                            <button
                                onClick={onBack}
                                className="flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-left text-sm text-slate-600 hover:bg-slate-100"
                            >
                                <span className="text-base">🏠</span>
                                Home
                            </button>

                            <button className="flex w-full items-center gap-3 rounded-2xl bg-blue-50 px-4 py-3 text-left text-sm font-medium text-blue-700">
                                <span className="text-base">📋</span>
                                Dashboard
                            </button>
                        </div>
                    </nav>
                </aside>

                <main className="flex-1 p-6 md:p-10">
                    <div className="mb-8 flex items-center justify-between rounded-3xl bg-white p-6 shadow-sm">
                        <div>
                            <h2 className="text-3xl font-bold tracking-tight text-slate-900">Professor / TA Dashboard</h2>
                            <p className="mt-2 text-sm text-slate-500">
                                View queue activity, see who is next, and serve students in order.
                            </p>
                        </div>

                        <button
                            onClick={onBack}
                            className="rounded-2xl border border-slate-200 px-5 py-3 text-sm font-medium text-slate-700 hover:bg-slate-50"
                        >
                            Return Home
                        </button>
                    </div>

                    {message && (
                        <div className="mb-6 rounded-2xl bg-blue-50 px-4 py-3 text-sm text-blue-700">
                            {message}
                        </div>
                    )}

                    {loading ? (
                        <p className="text-sm text-slate-500">Loading dashboard...</p>
                    ) : (

                        <section className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
                            <section className="mb-6 rounded-3xl bg-white p-6 shadow-sm">
                                <h3 className="text-xl font-semibold text-slate-900">Create Office Hours Session</h3>
                                <p className="mt-1 text-sm text-slate-500">
                                    Add a new office hours session that students can view on the homepage.
                                </p>

                                <form onSubmit={handleCreateSession} className="mt-5 grid gap-4 md:grid-cols-2">
                                    <input
                                        type="text"
                                        placeholder="Session host name"
                                        value={sessionForm.name}
                                        onChange={(e) => setSessionForm({ ...sessionForm, name: e.target.value })}
                                        className="rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-blue-500"
                                    />

                                    <select
                                        value={sessionForm.hostRole}
                                        onChange={(e) => setSessionForm({ ...sessionForm, hostRole: e.target.value })}
                                        className="rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-blue-500"
                                    >
                                        <option value="Professor">Professor</option>
                                        <option value="TA">TA</option>
                                    </select>

                                    <input
                                        type="text"
                                        placeholder="Subtitle (ex: Office Hours)"
                                        value={sessionForm.subtitle}
                                        onChange={(e) => setSessionForm({ ...sessionForm, subtitle: e.target.value })}
                                        className="rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-blue-500"
                                    />

                                    <input
                                        type="text"
                                        placeholder="Time (ex: Mon / Wed • 2:00 PM - 4:00 PM)"
                                        value={sessionForm.time}
                                        onChange={(e) => setSessionForm({ ...sessionForm, time: e.target.value })}
                                        className="rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-blue-500"
                                    />

                                    <input
                                        type="text"
                                        placeholder="Location"
                                        value={sessionForm.location}
                                        onChange={(e) => setSessionForm({ ...sessionForm, location: e.target.value })}
                                        className="rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-blue-500"
                                    />

                                    <input
                                        type="text"
                                        placeholder="Meeting type"
                                        value={sessionForm.meetingType}
                                        onChange={(e) => setSessionForm({ ...sessionForm, meetingType: e.target.value })}
                                        className="rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-blue-500"
                                    />

                                    <textarea
                                        placeholder="Description"
                                        value={sessionForm.description}
                                        onChange={(e) => setSessionForm({ ...sessionForm, description: e.target.value })}
                                        className="md:col-span-2 rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-blue-500"
                                        rows={3}
                                    />

                                    <div className="md:col-span-2">
                                        <button
                                            type="submit"
                                            className="rounded-2xl bg-blue-600 px-5 py-3 text-sm font-medium text-white shadow-sm hover:bg-blue-700"
                                        >
                                            Create Session
                                        </button>
                                    </div>
                                </form>
                            </section>
                            <div className="space-y-6">
                                <section className="rounded-3xl bg-white p-6 shadow-sm">
                                    <h3 className="text-xl font-semibold text-slate-900">Queue Counts</h3>

                                    {counts && (
                                        <div className="mt-4 space-y-3 text-sm text-slate-600">
                                            <p><span className="font-medium text-slate-900">DSL Queue:</span> {counts.DSL}</p>
                                            <p><span className="font-medium text-slate-900">Non-DSL Queue:</span> {counts["Non-DSL"]}</p>
                                            <p><span className="font-medium text-slate-900">Total:</span> {counts.Total}</p>
                                        </div>
                                    )}
                                </section>

                                <section className="rounded-3xl bg-white p-6 shadow-sm">
                                    <h3 className="text-xl font-semibold text-slate-900">Next Student</h3>

                                    <div className="mt-4 space-y-3 text-sm text-slate-600">
                                        {!nextStudent && (
                                            <p>No students are currently waiting.</p>
                                        )}

                                        {nextStudent && (
                                            <>
                                                <p><span className="font-medium text-slate-900">Name:</span> {nextStudent.student_name}</p>
                                                <p><span className="font-medium text-slate-900">Student ID:</span> {nextStudent.student_id}</p>
                                                <p><span className="font-medium text-slate-900">Topic:</span> {nextStudent.title}</p>
                                                <p><span className="font-medium text-slate-900">Joined At:</span> {nextStudent.joined_at}</p>
                                            </>
                                        )}

                                        <div className="pt-2">
                                            <button
                                                onClick={handleServeNext}
                                                className="rounded-2xl bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
                                            >
                                                Serve Next Student
                                            </button>
                                        </div>
                                    </div>
                                </section>
                            </div>

                            <section className="rounded-3xl bg-white p-6 shadow-sm">
                                <div className="mb-5 flex items-center justify-between">
                                    <div>
                                        <h3 className="text-xl font-semibold text-slate-900">Current Queue</h3>
                                        <p className="mt-1 text-sm text-slate-500">
                                            Students are shown in the same order they would be served.
                                        </p>
                                    </div>
                                </div>

                                <div className="space-y-4">
                                    {queue.length === 0 && (
                                        <p className="text-sm text-slate-500">No students are currently waiting.</p>
                                    )}

                                    {queue.map((student, index) => (
                                        <div
                                            key={student.request_id}
                                            className="rounded-3xl border border-slate-200 p-5"
                                        >
                                            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                                                <div>
                                                    <h4 className="text-lg font-semibold text-slate-900">
                                                        {index + 1}. {student.student_name}
                                                    </h4>
                                                    <p className="text-sm text-slate-500">
                                                        {student.student_id} • {student.title}
                                                    </p>
                                                </div>

                                                <div className="flex flex-wrap items-center gap-3">
                                                    <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
                                                        {student.is_dsl_queue ? "DSL" : "Non-DSL"}
                                                    </span>
                                                    <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
                                                        Joined: {student.joined_at}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </section>
                        </section>
                    )}
                </main>
            </div>
        </div>
    );
}