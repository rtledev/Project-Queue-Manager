// Import hooks from React.
// useState lets this component store values that can change while the app is running.
// useEffect lets this component run code automatically after rendering,
// which is useful for loading backend data when the page opens.
import { useEffect, useState } from "react";

// Import smaller UI components used by this page.
// Splitting the page this way keeps the backend/data logic here,
// while moving larger visual sections into their own files.
import LoginPage from "./components/LoginPage";
import OfficeHoursList from "./components/OfficeHoursList";
import QueueStatusCard from "./components/QueueStatusCard";
import HomeInfoCards from "./components/HomeInfoCards";
import DashboardPage from "./components/DashboardPage";
import ProfilePage from "./components/ProfilePage";

// HomePage is the main student-facing homepage.
// It receives four props:
// onLogin -> switches to the login/signup page
// onOpenDashboard -> switches to the professor / TA dashboard page
// currentStudent -> the currently signed-in student account
// onLogout -> clears the current student and logs them out
function HomePage({ onLogin, onOpenDashboard, onOpenProfile, currentStudent, onLogout }) {
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
      situation as a major user-facing error. That keeps the homepage cleaner on first load
      or after logout/cancellation.
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
      useEffect runs after the component is first rendered and whenever
      currentStudent changes.

      We use it here to:
      1. load the office-hours cards from the backend
      2. restore queue status for the currently signed-in student

      If no student is signed in, the homepage still loads office hours,
      but the queue status card is cleared.
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
              signed-in student already has an active queue request in the backend.

              This allows the Queue Status card to reappear after a browser refresh
              as long as the backend still has that student in memory.
            */
            if (currentStudent?.cwid) {
                await fetchQueueStatus(currentStudent.cwid);
            } else {
                setQueueStatus(null);
                setStatusError("");
            }
        }

        loadPageData();
    }, [currentStudent]);

    /*
      handleJoinQueue sends a POST request to the backend when the user clicks
      the "Join Queue" button for a session.

      This version no longer uses a hard-coded test student.
      Instead, it uses the currently signed-in student account.

      If no student is signed in yet, the user is prompted to log in or create an account first.
    */
    async function handleJoinQueue(person) {
        if (!currentStudent) {
            setJoinMessage("Please log in or create an account before joining the queue.");
            return;
        }
        if (currentStudent.role === "professor") {
            setJoinMessage("Professor accounts cannot join the student queue.");
            return;
        }

        try {
            setJoinMessage("");
            setStatusError("");

            const response = await fetch("http://127.0.0.1:5000/api/join-queue", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    student_id: currentStudent.cwid,
                    student_name: `${currentStudent.first_name} ${currentStudent.last_name}`.trim(),
                    email: currentStudent.contact_email || currentStudent.school_email,
                    title: `Help session with ${person.name}`,
                    notification_ok: true,
                    group_ok: true,
                    is_dsl_queue: currentStudent.dsl_status,
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
            await fetchQueueStatus(currentStudent.cwid);

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

      This version uses the currently signed-in student account.

      If cancellation succeeds:
      - a success message is shown
      - the local queue status card is cleared
      - office-hours counts are refreshed from the backend
    */
    async function handleCancelQueue() {
        if (!currentStudent) {
            setJoinMessage("Please log in before cancelling a queue request.");
            return;
        }

        try {
            setJoinMessage("");
            setStatusError("");

            const response = await fetch("http://127.0.0.1:5000/api/cancel-queue", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    student_id: currentStudent.cwid,
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
        // Outer wrapper for the homepage.
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

                            {/*
                            Profile navigation button.
                            Clicking this button calls onOpenProfile.
                            onOpenProfile is provided by the parent component and changes
                            the current page to the student's profile page.
                            */}
                            <button
                                onClick={onOpenProfile}
                                className="flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-left text-sm text-slate-600 hover:bg-slate-100"
                            >
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

                        {/* Welcome text and signed-in student label */}
                        <div>
                            <h2 className="text-3xl font-bold tracking-tight text-slate-900">Welcome to Ps &amp; Qs</h2>
                            <p className="mt-2 max-w-2xl text-sm text-slate-500 md:text-base">
                                Browse office hours, review session details, join the queue, and track your position in one place.
                            </p>

                            {/*
                              If a student is currently signed in, show their name below the welcome text.
                            */}
                            {currentStudent && (
                                <p className="mt-3 text-sm text-slate-600">
                                    Signed in as{" "}
                                    <span className="font-medium text-slate-900">
                                        {currentStudent.first_name} {currentStudent.last_name}
                                    </span>
                                </p>
                            )}
                        </div>

                        {/* Action buttons */}
                        <div className="flex gap-3">

                            {/*
                              If no student is signed in, show the login/signup button.

                              onLogin is provided by the parent component and changes
                              the current page to the authentication page.
                            */}
                            {!currentStudent ? (
                                <button
                                    onClick={onLogin}
                                    className="rounded-2xl border border-slate-200 px-5 py-3 text-sm font-medium text-slate-700 hover:bg-slate-50"
                                >
                                    Log In / Sign Up
                                </button>
                            ) : (
                                /*
                                  If a student is already signed in, replace the login button
                                  with a logout button.

                                  onLogout is provided by the parent component and clears
                                  the current student from app state and localStorage.
                                */
                                <button
                                    onClick={onLogout}
                                    className="rounded-2xl border border-slate-200 px-5 py-3 text-sm font-medium text-slate-700 hover:bg-slate-50"
                                >
                                    Log Out
                                </button>
                            )}
                            {/*
                            Clicking this button calls onOpenProfile.
                            onOpenProfile is provided by the parent component and changes
                            the current page to the student's profile page.
                            */}
                            <button
                                onClick={onOpenProfile}
                                className="rounded-2xl border border-slate-200 px-5 py-3 text-sm font-medium text-slate-700 hover:bg-slate-50"
                            >
                                Open Profile
                            </button>

                            {/*
                            Only professor accounts should see the dashboard button,
                            since the dashboard contains student queue information meant for staff use.
                            */}
                            {currentStudent?.role === "professor" && (
                                <button
                                    onClick={onOpenDashboard}
                                    className="rounded-2xl border border-slate-200 px-5 py-3 text-sm font-medium text-slate-700 hover:bg-slate-50"
                                >
                                    Open Dashboard
                                </button>
                            )}


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

                    {/* Main content area split into two columns */}
                    <section className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">

                        {/* Left column: available office hours cards */}
                        <OfficeHoursList
                            officeHours={officeHours}
                            loading={loading}
                            error={error}
                            onJoinQueue={handleJoinQueue}
                            currentStudent={currentStudent}
                            queueStatus={queueStatus}
                        />

                        {/* Right column: queue status and informational cards */}
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
// It controls which page to show and stores the currently authenticated student.
export default function PsNQsHomepage() {
    /*
      currentStudent stores the signed-in student account for the current browser session.

      We initialize it from localStorage so the app can remember who is logged in
      even after a browser refresh.
    */
    const [currentStudent, setCurrentStudent] = useState(() => {
        const savedStudent = localStorage.getItem("psnqs_current_student");
        return savedStudent ? JSON.parse(savedStudent) : null;
    });


    /*
      page is a state variable.
      setPage is the function used to change page.
      The initial value is "home", so the app starts on the home page.
    */
    const [page, setPage] = useState("home");

    /*
      handleLoginSuccess is called after either:
      - a successful login
      - a successful signup

      It stores the student in React state and in localStorage,
      then returns the user to the homepage.
    */
    function handleLoginSuccess(student) {
        setCurrentStudent(student);
        localStorage.setItem("psnqs_current_student", JSON.stringify(student));
        setPage("home");
    }

    /*
   handleProfileUpdated is called after the Profile page successfully saves changes.

   It updates the current student in both React state and localStorage
   so the homepage and other pages immediately reflect the newest profile data.
   */
    function handleProfileUpdated(student) {
        setCurrentStudent(student);
        localStorage.setItem("psnqs_current_student", JSON.stringify(student));
    }

    /*
      handleLogout clears the current student from both React state and localStorage,
      then returns the user to the homepage.
    */
    function handleLogout() {
        setCurrentStudent(null);
        localStorage.removeItem("psnqs_current_student");
        setPage("home");
    }

    /*
      Conditional rendering:
      If page is equal to "login", render the LoginPage component.

      onBack is passed down so LoginPage can switch the page back to "home".
      onLoginSuccess is passed down so LoginPage can send the authenticated
      student account back to this parent component.
    */
    if (page === "login") {
        return (
            <LoginPage
                onBack={() => setPage("home")}
                onLoginSuccess={handleLoginSuccess}
            />
        );
    }

    /*
        If page is equal to "profile", render the ProfilePage component.

        currentStudent is passed down so the page can load the correct student profile.
        onBack is passed down so ProfilePage can switch back to the home page.
        onProfileUpdated is passed down so ProfilePage can send the updated
        student object back to this parent component after a successful save.
        onLogout is passed down so the user can log out directly from the profile page.
    */
    if (page === "profile") {
        return (
            <ProfilePage
                currentStudent={currentStudent}
                onBack={() => setPage("home")}
                onProfileUpdated={handleProfileUpdated}
                onLogout={handleLogout}
            />
        );
    }

    /*
      If page is equal to "dashboard", render the DashboardPage component.
      onBack is passed down so DashboardPage can switch the page back to "home".
    */
    if (page === "dashboard") {
        if (currentStudent?.role !== "professor") {
            return (
                <HomePage
                    onLogin={() => setPage("login")}
                    onOpenDashboard={() => setPage("dashboard")}
                    onOpenProfile={() => setPage("profile")}
                    currentStudent={currentStudent}
                    onLogout={handleLogout}
                />
            );
        }

        return (
            <DashboardPage
                onBack={() => setPage("home")}
                currentStudent={currentStudent}
            />
        );
    }

    /*
      If neither condition above is true, render the HomePage component.

      onLogin is passed down so HomePage can switch the page to the auth page.
      onOpenDashboard is passed down so HomePage can switch the page to the dashboard.
      onOpenProfile is passed down so HomePage can switch the page to the profile page.
      currentStudent is passed down so HomePage can use the signed-in student for queue actions.
      onLogout is passed down so HomePage can log the current student out.
    */
    return (
        <HomePage
            onLogin={() => setPage("login")}
            onOpenDashboard={() => setPage("dashboard")}
            onOpenProfile={() => setPage("profile")}
            currentStudent={currentStudent}
            onLogout={handleLogout}
        />
    );
}