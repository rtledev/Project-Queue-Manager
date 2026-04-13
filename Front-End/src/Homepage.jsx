// Import hooks from React.
// useState lets this component store values that can change over time.
// useEffect lets this component run code automatically after the component renders,
// which is useful for things like fetching data from the backend API.
import { useEffect, useState } from "react";

// Import smaller UI components used by this page.
// Splitting the page this way keeps the logic here while moving
// large visual sections into their own files.
import LoginPage from "./components/LoginPage";
import OfficeHoursList from "./components/OfficeHoursList";
import QueueStatusCard from "./components/QueueStatusCard";
import HomeInfoCards from "./components/HomeInfoCards";
import DashboardPage from "./components/DashboardPage";

// HomePage is a separate component responsible for rendering the homepage.
// It receives two props:
// onLogin -> switches to the login page
// onOpenDashboard -> switches to the professor / TA dashboard page
function HomePage({ onLogin, onOpenDashboard }) {

    /*
      TEST_STUDENT_ID is a temporary hard-coded student identifier used during
      frontend/backend testing.

      Right now, this acts as the "current student" for queue actions and
      queue status lookup.

      Later, this should come from:
      - a real login system
      - session data
      - or the student's saved profile/account information
    */
    const TEST_STUDENT_ID = "12345678";

    /*
      officeHours stores the list of office-hours sessions returned by the backend API.
      It starts as an empty array because no data has been loaded yet.

      loading tracks whether the frontend is currently waiting for the backend response.
      This helps us show a loading message while data is being fetched.

      error stores any error message if the API request fails.
      If the request works, error stays as an empty string.

      joinMessage stores the message shown after trying to join or cancel the queue.
      It can show either a success message or an error message.

      queueStatus stores the currently tracked student's queue information.
      If null, the student is not currently being shown in the status card.

      statusError stores any error related specifically to queue status lookup.
    */
    const [officeHours, setOfficeHours] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");
    const [joinMessage, setJoinMessage] = useState("");
    const [queueStatus, setQueueStatus] = useState(null);
    const [statusError, setStatusError] = useState("");

    /*
      fetchQueueStatus requests the current queue position for one student ID.

      If the backend finds an active request, queueStatus is updated with the response.

      If no active request exists, we quietly clear the card instead of treating that
      situation as a major user-facing error. That keeps the homepage cleaner on first load.
    */
    async function fetchQueueStatus(studentId) {
        try {
            setStatusError("");

            const response = await fetch(
                `http://127.0.0.1:5000/api/queue/${studentId}/position`
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Unable to fetch queue status.");
            }

            setQueueStatus(data);
        } catch (err) {
            /*
              If the student is not currently in the queue, we simply clear the
              queue status display.

              For this prototype, that is expected behavior and does not need to be
              shown as a visible red error message.
            */
            setQueueStatus(null);
            setStatusError("");
        }
    }

    /*
      useEffect runs after the component is first rendered.

      We use it here to load the homepage data from the backend when the page first opens.

      On initial page load, we do two things:
      1. fetch the office-hours cards
      2. try to restore the queue status for the current test student

      The empty dependency array [] means this runs only once when the page first loads,
      not every single time the component re-renders.
    */
    useEffect(() => {
        async function loadPageData() {
            try {
                setLoading(true);
                setError("");

                const response = await fetch("http://127.0.0.1:5000/api/office-hours");

                if (!response.ok) {
                    throw new Error("Failed to fetch office hours.");
                }

                const data = await response.json();
                setOfficeHours(data);
            } catch (err) {
                setError(err.message);
            } finally {
                setLoading(false);
            }

            /*
              After loading the office-hours data, also check whether the current
              test student already has an active queue request in the backend.

              This allows the Queue Status card to reappear after a browser refresh
              as long as the backend server still has that student in memory.
            */
            await fetchQueueStatus(TEST_STUDENT_ID);
        }

        loadPageData();
    }, []);

    /*
      handleJoinQueue sends a POST request to the backend when the user clicks
      the "Join Queue" button for a session.

      For now, this uses temporary test student data so we can confirm the
      frontend and backend are connected correctly.

      Later, this data should come from:
      - the logged-in student
      - a join form
      - or student profile information stored in the system
    */
    async function handleJoinQueue(person) {
        try {
            setJoinMessage("");
            setStatusError("");

            const response = await fetch("http://127.0.0.1:5000/api/join-queue", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    student_id: TEST_STUDENT_ID,
                    student_name: "Israel Zavala",
                    email: "name@csu.fullerton.edu",
                    title: `Help session with ${person.name}`,
                    notification_ok: true,
                    group_ok: true,
                    is_dsl_queue: false,
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Unable to join queue.");
            }

            setJoinMessage(
                `Successfully joined the queue for ${person.name}. Your current position is ${data.position}.`
            );

            /*
              After a successful join, immediately fetch the student's latest queue status
              so the status card updates with the current position.
            */
            await fetchQueueStatus(TEST_STUDENT_ID);

            /*
              Refresh office-hours data after joining so the waiting counts shown on the page
              stay in sync with the backend.
            */
            const refreshResponse = await fetch("http://127.0.0.1:5000/api/office-hours");
            const refreshedData = await refreshResponse.json();
            setOfficeHours(refreshedData);

        } catch (err) {
            setJoinMessage(err.message || "Something went wrong while joining the queue.");
        }
    }

    /*
      handleCancelQueue sends a POST request to the backend when the user clicks
      the cancel button inside the Queue Status card.

      If cancellation succeeds:
      - a success message is shown
      - the local queue status card is cleared
      - office-hours counts are refreshed from the backend

      This completes the basic student-side flow:
      join -> view status -> cancel
    */
    async function handleCancelQueue() {
        try {
            setJoinMessage("");
            setStatusError("");

            const response = await fetch("http://127.0.0.1:5000/api/cancel-queue", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    student_id: TEST_STUDENT_ID,
                }),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Unable to cancel queue request.");
            }

            // Show success confirmation to the user.
            setJoinMessage("Your queue request was cancelled successfully.");

            // Clear the queue status card because the student is no longer waiting.
            setQueueStatus(null);

            // Refresh office-hours data so waiting counts stay in sync with the backend.
            const refreshResponse = await fetch("http://127.0.0.1:5000/api/office-hours");
            const refreshedData = await refreshResponse.json();
            setOfficeHours(refreshedData);

        } catch (err) {
            setJoinMessage(err.message || "Something went wrong while cancelling the queue.");
        }
    }

    return (
        // Outer wrapper for the homepage
        <div className="min-h-screen bg-slate-100 text-slate-800">

            {/* Main page layout container */}
            <div className="mx-auto flex min-h-screen max-w-7xl">

                {/* Sidebar for the homepage */}
                <aside className="hidden w-64 flex-col border-r border-slate-200 bg-white lg:flex">

                    {/* Branding section */}
                    <div className="border-b border-slate-200 px-8 py-8">
                        <h1 className="text-3xl font-bold tracking-tight text-slate-900">PsNQs</h1>
                        <p className="mt-2 text-sm text-slate-500">Meeting Queue Manager</p>
                    </div>

                    {/* Sidebar navigation */}
                    <nav className="flex-1 px-4 py-6">
                        <div className="space-y-2">

                            {/* Active page button */}
                            <button className="flex w-full items-center gap-3 rounded-2xl bg-blue-50 px-4 py-3 text-left text-sm font-medium text-blue-700">
                                <span className="text-base">📅</span>
                                Home
                            </button>

                            {/* Placeholder navigation button */}
                            <button className="flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-left text-sm text-slate-600 hover:bg-slate-100">
                                <span className="text-base">🕒</span>
                                Office Hours
                            </button>

                            {/* Placeholder navigation button */}
                            <button className="flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-left text-sm text-slate-600 hover:bg-slate-100">
                                <span className="text-base">👤</span>
                                Profile
                            </button>
                        </div>
                    </nav>
                </aside>

                {/* Main homepage content */}
                <main className="flex-1 p-6 md:p-10">

                    {/*
                      Top hero/welcome banner.
                      md:flex-row means on medium screens and up, the text and buttons appear side by side.
                    */}
                    <div className="mb-8 flex flex-col gap-4 rounded-3xl bg-white p-6 shadow-sm md:flex-row md:items-center md:justify-between">

                        {/* Welcome text */}
                        <div>
                            <h2 className="text-3xl font-bold tracking-tight text-slate-900">Welcome to Ps &amp; Qs</h2>
                            <p className="mt-2 max-w-2xl text-sm text-slate-500 md:text-base">
                                Join office hours, view available staff, and keep track of your queue position in one place.
                            </p>
                        </div>

                        {/* Action buttons */}
                        <div className="flex gap-3">

                            {/*
                              Clicking this button calls onLogin.
                              onLogin is provided by the parent component and changes the current page to "login".
                            */}
                            <button
                                onClick={onLogin}
                                className="rounded-2xl border border-slate-200 px-5 py-3 text-sm font-medium text-slate-700 hover:bg-slate-50"
                            >
                                Log In
                            </button>

                            {/*
                              Clicking this button calls onOpenDashboard.
                              onOpenDashboard is provided by the parent component and changes
                              the current page to the professor / TA dashboard.
                            */}
                            <button
                                onClick={onOpenDashboard}
                                className="rounded-2xl border border-slate-200 px-5 py-3 text-sm font-medium text-slate-700 hover:bg-slate-50"
                            >
                                Open Dashboard
                            </button>

                            {/* Placeholder button for future onboarding or registration flow */}
                            <button className="rounded-2xl bg-blue-600 px-5 py-3 text-sm font-medium text-white shadow-sm hover:bg-blue-700">
                                Get Started
                            </button>
                        </div>
                    </div>

                    {/*
                      joinMessage is used for both queue join results and queue cancel results.
                      This allows one shared banner area to communicate success or failure to the user.
                    */}
                    {joinMessage && (
                        <div className="mb-6 rounded-2xl bg-blue-50 px-4 py-3 text-sm text-blue-700">
                            {joinMessage}
                        </div>
                    )}

                    <section className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">

                        {/* Left column: available office hours cards */}
                        <OfficeHoursList
                            officeHours={officeHours}
                            loading={loading}
                            error={error}
                            onJoinQueue={handleJoinQueue}
                        />

                        {/* Right column: informational sections and live queue status */}
                        <div className="space-y-6">
                            <QueueStatusCard
                                queueStatus={queueStatus}
                                statusError={statusError}
                                onCancelQueue={handleCancelQueue}
                            />

                            <HomeInfoCards />
                        </div>
                    </section>
                </main>
            </div>
        </div>
    );
}

// This is the main exported component for the file.
// It controls which page to show.
//
// page is a state variable.
// setPage is the function used to change page.
// The initial value is "home", so the app starts on the home page.
export default function PsNQsHomepage() {
    const [page, setPage] = useState("home");

    /*
      Conditional rendering:
      If page is equal to "login", render the LoginPage component.
      onBack is passed down so LoginPage can switch the page back to "home".
    */
    if (page === "login") {
        return <LoginPage onBack={() => setPage("home")} />;
    }

    /*
      If page is equal to "dashboard", render the DashboardPage component.
      onBack is passed down so DashboardPage can switch the page back to "home".
    */
    if (page === "dashboard") {
        return <DashboardPage onBack={() => setPage("home")} />;
    }

    /*
      If neither condition above is true, render the HomePage component.

      onLogin is passed down so HomePage can switch the page to "login".
      onOpenDashboard is passed down so HomePage can switch the page to "dashboard".
    */
    return (
        <HomePage
            onLogin={() => setPage("login")}
            onOpenDashboard={() => setPage("dashboard")}
        />
    );
}