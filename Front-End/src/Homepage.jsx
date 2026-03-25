// Import the useState hook from React.
// useState lets this component store data that can change while the app is running.
import { useState } from "react";

// LoginPage is a separate component responsible for rendering the login screen.
// It receives one prop: onBack.
// onBack is a function passed in from the parent so this page can switch back to the home page.
function LoginPage({ onBack }) {
    return (
        // Outer wrapper for the whole login page.
        // min-h-screen makes the page at least the full height of the screen.
        // bg-slate-100 sets the background color.
        // text-slate-800 sets the default text color.
        <div className="min-h-screen bg-slate-100 text-slate-800">

            {/* 
               Main page layout container.
               mx-auto centers the container horizontally.
               flex makes the sidebar and main content sit side by side.
               max-w-7xl limits the overall width so the page does not stretch too far.
            */}
            <div className="mx-auto flex min-h-screen max-w-7xl">

                {/*
                  Sidebar area.
                  hidden means it is hidden on small screens.
                  lg:flex means it becomes visible and uses flex layout on large screens and up.
                  w-64 gives the sidebar a fixed width.
                */}
                <aside className="hidden w-64 flex-col border-r border-slate-200 bg-white lg:flex">

                    {/* Branding / logo section at the top of the sidebar */}
                    <div className="border-b border-slate-200 px-8 py-8">
                        <h1 className="text-3xl font-bold tracking-tight text-slate-900">PsNQs</h1>
                        <p className="mt-2 text-sm text-slate-500">Meeting Queue Manager</p>
                    </div>

                    {/* Navigation area inside the sidebar */}
                    <nav className="flex-1 px-4 py-6">
                        <div className="space-y-2">

                            {/*
                              Home button.
                              When clicked, it calls onBack.
                              onBack comes from the parent component and changes the page back to "home".
                            */}
                            <button
                                onClick={onBack}
                                className="flex w-full items-center gap-3 rounded-2xl px-4 py-3 text-left text-sm text-slate-600 hover:bg-slate-100"
                            >
                                <span className="text-base">🏠</span>
                                Home
                            </button>

                            {/*
                              Login button in the sidebar.
                              This one is styled as the active/current page.
                              It does not need an onClick here because the user is already on the login page.
                            */}
                            <button className="flex w-full items-center gap-3 rounded-2xl bg-blue-50 px-4 py-3 text-left text-sm font-medium text-blue-700">
                                <span className="text-base">🔐</span>
                                Log In
                            </button>
                        </div>
                    </nav>
                </aside>

                {/*
                  Main content area for the login card.
                  flex-1 makes it take the remaining width not used by the sidebar.
                  items-center and justify-center center the login box vertically and horizontally.
                */}
                <main className="flex flex-1 items-center justify-center p-6 md:p-10">

                    {/* Login form card */}
                    <div className="w-full max-w-md rounded-3xl bg-white p-8 shadow-sm">

                        {/* Heading section inside the card */}
                        <div className="mb-8 text-center">
                            <h2 className="text-3xl font-bold tracking-tight text-slate-900">Welcome Back</h2>
                            <p className="mt-2 text-sm text-slate-500">
                                Sign in to view your queue status, meetings, and profile.
                            </p>
                        </div>

                        {/*
                          Form element for login inputs.
                          Right now, this is only visual.
                          It does not yet have any state variables, submit handler, or backend connection.
                        */}
                        <form className="space-y-5">

                            {/* Email input group */}
                            <div>
                                <label className="mb-2 block text-sm font-medium text-slate-700">School Email</label>
                                <input
                                    type="email"
                                    placeholder="name@csu.fullerton.edu"
                                    className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-blue-500"
                                />
                            </div>

                            {/* Password input group */}
                            <div>
                                <label className="mb-2 block text-sm font-medium text-slate-700">Password</label>
                                <input
                                    type="password"
                                    placeholder="Enter your password"
                                    className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-blue-500"
                                />
                            </div>

                            {/*
                              Row containing the "Remember me" checkbox and the "Forgot password?" button.
                              justify-between places them on opposite sides of the row.
                            */}
                            <div className="flex items-center justify-between text-sm">
                                <label className="flex items-center gap-2 text-slate-600">
                                    <input type="checkbox" className="rounded" />
                                    Remember me
                                </label>

                                {/*
                                  type="button" is important here.
                                  Without it, a button inside a form defaults to type="submit".
                                  This button should not submit the form.
                                */}
                                <button type="button" className="font-medium text-blue-600 hover:text-blue-700">
                                    Forgot password?
                                </button>
                            </div>

                            {/*
                              Submit button for the login form.
                              type="submit" tells the browser this button submits the form.
                              Since no onSubmit handler exists yet, this is still just part of the UI.
                            */}
                            <button
                                type="submit"
                                className="w-full rounded-2xl bg-blue-600 px-5 py-3 text-sm font-medium text-white shadow-sm hover:bg-blue-700"
                            >
                                Log In
                            </button>
                        </form>

                        {/*
                          Bottom text and back button.
                          Clicking "Return home" also calls onBack to switch pages.
                        */}
                        <div className="mt-6 text-center text-sm text-slate-500">
                            Need to go back?{" "}
                            <button onClick={onBack} className="font-medium text-blue-600 hover:text-blue-700">
                                Return home
                            </button>
                        </div>
                    </div>
                </main>
            </div>
        </div>
    );
}

// HomePage is a separate component responsible for rendering the homepage.
// It receives one prop: onLogin.
// onLogin is a function passed from the parent so this page can switch to the login page.
function HomePage({ onLogin }) {

    {/*
      Temporary local data for office hours cards.
      This is hard-coded for now.
      Later, this would come from the api/backend .
    */}
    const officeHours = [
        {
            name: "Professor Jones",
            role: "Professor",
            studentsWaiting: 4,
            status: "Open",
            subtitle: "Office Hours",
        },
        {
            name: "TA Smith",
            role: "TA",
            studentsWaiting: 2,
            status: "Open",
            subtitle: "Lab Help",
        },
    ];

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

                            {/* Placeholder button for future onboarding or registration flow */}
                            <button className="rounded-2xl bg-blue-600 px-5 py-3 text-sm font-medium text-white shadow-sm hover:bg-blue-700">
                                Get Started
                            </button>
                        </div>
                    </div>

                    {/*
                      Main content section split into two columns on large screens.
                      Left column is wider than the right column.
                    */}
                    <section className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">

                        {/* Left column: available office hours cards */}
                        <div className="rounded-3xl bg-white p-6 shadow-sm">

                            {/* Header row for office hours section */}
                            <div className="mb-5 flex items-center justify-between">
                                <div>
                                    <h3 className="text-xl font-semibold text-slate-900">Available Office Hours</h3>
                                    <p className="mt-1 text-sm text-slate-500">Browse open sessions and join the queue.</p>
                                </div>

                                {/* Placeholder button for future expansion */}
                                <button className="rounded-2xl border border-slate-200 px-4 py-2 text-sm text-slate-600 hover:bg-slate-50">
                                    View All
                                </button>
                            </div>

                            {/* Stack of office hours cards */}
                            <div className="space-y-4">

                                {/*
                                  Loop over each object inside officeHours.
                                  For each object, create one card.
                                  person is the current object being processed.
                                */}
                                {officeHours.map((person) => (
                                    <div
                                        key={person.name}
                                        className="rounded-3xl border border-slate-200 p-5 transition hover:shadow-md"
                                    >
                                        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">

                                            {/* Left side of the card: icon + basic information */}
                                            <div className="flex items-center gap-4">

                                                {/* Placeholder avatar/icon */}
                                                <div className="flex h-14 w-14 items-center justify-center rounded-full bg-slate-200 text-xl">
                                                    👤
                                                </div>

                                                {/* Name and subtitle */}
                                                <div>
                                                    <h4 className="text-lg font-semibold text-slate-900">{person.name}</h4>
                                                    <p className="text-sm text-slate-500">
                                                        {person.role} • {person.subtitle}
                                                    </p>
                                                </div>
                                            </div>

                                            {/* Right side of the card: status + queue count + action */}
                                            <div className="flex flex-wrap items-center gap-3">

                                                {/* Status badge */}
                                                <span className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
                                                    {person.status}
                                                </span>

                                                {/* Number of waiting students */}
                                                <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
                                                    {person.studentsWaiting} waiting
                                                </span>

                                                {/* Placeholder join action */}
                                                <button className="rounded-2xl bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700">
                                                    Join Queue
                                                </button>
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        {/* Right column: informational sections */}
                        <div className="space-y-6">

                            {/* "How It Works" card */}
                            <section className="rounded-3xl bg-white p-6 shadow-sm">
                                <h3 className="text-xl font-semibold text-slate-900">How It Works</h3>

                                <div className="mt-5 space-y-4">

                                    {/*
                                      Loop through an array of instruction strings.
                                      index is the numeric position of each item (0, 1, 2, 3).
                                      index + 1 is used so the UI shows 1, 2, 3, 4 instead of 0, 1, 2, 3.
                                    */}
                                    {[
                                        "Create or log into your account",
                                        "Choose an office hours session",
                                        "Join the queue and track your position",
                                        "Meet with your professor or TA",
                                    ].map((step, index) => (
                                        <div key={step} className="flex items-start gap-3">

                                            {/* Step number circle */}
                                            <div className="mt-0.5 flex h-8 w-8 items-center justify-center rounded-full bg-blue-600 text-sm font-semibold text-white">
                                                {index + 1}
                                            </div>

                                            {/* Step description */}
                                            <p className="text-sm leading-6 text-slate-600">{step}</p>
                                        </div>
                                    ))}
                                </div>
                            </section>

                            {/* "Why Ps & Qs?" card */}
                            <section className="rounded-3xl bg-slate-900 p-6 text-white shadow-sm">
                                <h3 className="text-xl font-semibold">Why Ps &amp; Qs?</h3>

                                <div className="mt-4 space-y-3 text-sm text-slate-300">
                                    <p>• Cleaner queue management for office hours</p>
                                    <p>• Easy student access to available meetings</p>
                                    <p>• Future support for grouping, scheduling, and notifications</p>
                                </div>
                            </section>
                        </div>
                    </section>
                </main>
            </div>
        </div>
    );
}

// This is the main exported component for the file.
// It controls which page to show.
export default function PsNQsHomepage() {

    {/*
      page is a state variable.
      setPage is the function used to change page.
      The initial value is "home", so the app starts on the home page.
    */}
    const [page, setPage] = useState("home");

    {/*
      Conditional rendering:
      If page is equal to "login", render the LoginPage component.
      onBack is passed down so LoginPage can switch the page back to "home".
    */}
    if (page === "login") {
        return <LoginPage onBack={() => setPage("home")} />;
    }

    {/*
      If the condition above is not true, render the HomePage component.
      onLogin is passed down so HomePage can switch the page to "login".
    */}
    return <HomePage onLogin={() => setPage("login")} />;
}