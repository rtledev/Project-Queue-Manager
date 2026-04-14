import { useState } from "react";

// LoginPage is the authentication page for the app.
// It supports two modes:
// 1. login
// 2. sign up
//
// It receives two props:
// onBack -> returns the user to the homepage
// onLoginSuccess -> sends the authenticated student back to the parent component
export default function LoginPage({ onBack, onLoginSuccess }) {

    /*
      mode controls whether the card is showing the login form
      or the sign-up form.
    */
    const [mode, setMode] = useState("login");

    /*
      message stores success or error feedback shown to the user.
    */
    const [message, setMessage] = useState("");

    /*
      loginForm stores the input values for the login flow.
    */
    const [loginForm, setLoginForm] = useState({
        cwid: "",
        school_email: "",
        password: "",
    });

    /*
      signupForm stores the input values for the sign-up flow.
    */
    const [signupForm, setSignupForm] = useState({
        cwid: "",
        first_name: "",
        middle_initial: "",
        last_name: "",
        school_email: "",
        contact_email: "",
        phone_number: "",
        dsl_status: false,
        password: "",
    });

    /*
      handleLoginSubmit sends the login form data to the backend.
      If authentication succeeds, the returned student object is
      passed back to the parent through onLoginSuccess.
    */
    async function handleLoginSubmit(event) {
        event.preventDefault();

        try {
            setMessage("");

            const response = await fetch("http://127.0.0.1:5000/api/auth/login", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(loginForm),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Unable to log in.");
            }

            setMessage("Login successful.");
            onLoginSuccess(data.student);
        } catch (err) {
            setMessage(err.message || "Something went wrong while logging in.");
        }
    }

    /*
      handleSignupSubmit sends the sign-up form data to the backend.
      If account creation succeeds, the new student object is passed
      back to the parent through onLoginSuccess so the user is effectively
      signed in immediately after signup.
    */
    async function handleSignupSubmit(event) {
        event.preventDefault();

        try {
            setMessage("");

            const response = await fetch("http://127.0.0.1:5000/api/auth/signup", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(signupForm),
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Unable to create account.");
            }

            setMessage("Account created successfully.");
            onLoginSuccess(data.student);
        } catch (err) {
            setMessage(err.message || "Something went wrong while creating the account.");
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
                                <span className="text-base">🔐</span>
                                {mode === "login" ? "Log In" : "Sign Up"}
                            </button>
                        </div>
                    </nav>
                </aside>

                <main className="flex flex-1 items-center justify-center p-6 md:p-10">
                    <div className="w-full max-w-md rounded-3xl bg-white p-8 shadow-sm">
                        <div className="mb-8 text-center">
                            <h2 className="text-3xl font-bold tracking-tight text-slate-900">
                                {mode === "login" ? "Welcome Back" : "Create Your Account"}
                            </h2>
                            <p className="mt-2 text-sm text-slate-500">
                                {mode === "login"
                                    ? "Log in to join the queue with your saved student account."
                                    : "Create an account so your queue requests use your real student information."}
                            </p>
                        </div>

                        <div className="mb-6 flex rounded-2xl bg-slate-100 p-1">
                            <button
                                onClick={() => setMode("login")}
                                className={`flex-1 rounded-2xl px-4 py-2 text-sm font-medium ${mode === "login"
                                        ? "bg-white text-slate-900 shadow-sm"
                                        : "text-slate-600"
                                    }`}
                            >
                                Log In
                            </button>
                            <button
                                onClick={() => setMode("signup")}
                                className={`flex-1 rounded-2xl px-4 py-2 text-sm font-medium ${mode === "signup"
                                        ? "bg-white text-slate-900 shadow-sm"
                                        : "text-slate-600"
                                    }`}
                            >
                                Sign Up
                            </button>
                        </div>

                        {message && (
                            <div className="mb-6 rounded-2xl bg-blue-50 px-4 py-3 text-sm text-blue-700">
                                {message}
                            </div>
                        )}

                        {mode === "login" ? (
                            <form className="space-y-5" onSubmit={handleLoginSubmit}>
                                <div>
                                    <label className="mb-2 block text-sm font-medium text-slate-700">CWID</label>
                                    <input
                                        type="text"
                                        value={loginForm.cwid}
                                        onChange={(e) =>
                                            setLoginForm({ ...loginForm, cwid: e.target.value })
                                        }
                                        placeholder="12345678"
                                        className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-blue-500"
                                    />
                                </div>

                                <div>
                                    <label className="mb-2 block text-sm font-medium text-slate-700">School Email</label>
                                    <input
                                        type="email"
                                        value={loginForm.school_email}
                                        onChange={(e) =>
                                            setLoginForm({ ...loginForm, school_email: e.target.value })
                                        }
                                        placeholder="name@csu.fullerton.edu"
                                        className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-blue-500"
                                    />
                                </div>

                                <div>
                                    <label className="mb-2 block text-sm font-medium text-slate-700">Password</label>
                                    <input
                                        type="password"
                                        value={loginForm.password}
                                        onChange={(e) =>
                                            setLoginForm({ ...loginForm, password: e.target.value })
                                        }
                                        placeholder="Enter your password"
                                        className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-blue-500"
                                    />
                                </div>

                                <button
                                    type="submit"
                                    className="w-full rounded-2xl bg-blue-600 px-5 py-3 text-sm font-medium text-white shadow-sm hover:bg-blue-700"
                                >
                                    Log In
                                </button>
                            </form>
                        ) : (
                            <form className="space-y-5" onSubmit={handleSignupSubmit}>
                                <div>
                                    <label className="mb-2 block text-sm font-medium text-slate-700">CWID</label>
                                    <input
                                        type="text"
                                        value={signupForm.cwid}
                                        onChange={(e) =>
                                            setSignupForm({ ...signupForm, cwid: e.target.value })
                                        }
                                        placeholder="12345678"
                                        className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-blue-500"
                                    />
                                </div>

                                <div>
                                    <label className="mb-2 block text-sm font-medium text-slate-700">First Name</label>
                                    <input
                                        type="text"
                                        value={signupForm.first_name}
                                        onChange={(e) =>
                                            setSignupForm({ ...signupForm, first_name: e.target.value })
                                        }
                                        className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-blue-500"
                                    />
                                </div>

                                <div>
                                    <label className="mb-2 block text-sm font-medium text-slate-700">Middle Initial</label>
                                    <input
                                        type="text"
                                        value={signupForm.middle_initial}
                                        onChange={(e) =>
                                            setSignupForm({ ...signupForm, middle_initial: e.target.value })
                                        }
                                        className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-blue-500"
                                    />
                                </div>

                                <div>
                                    <label className="mb-2 block text-sm font-medium text-slate-700">Last Name</label>
                                    <input
                                        type="text"
                                        value={signupForm.last_name}
                                        onChange={(e) =>
                                            setSignupForm({ ...signupForm, last_name: e.target.value })
                                        }
                                        className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-blue-500"
                                    />
                                </div>

                                <div>
                                    <label className="mb-2 block text-sm font-medium text-slate-700">School Email</label>
                                    <input
                                        type="email"
                                        value={signupForm.school_email}
                                        onChange={(e) =>
                                            setSignupForm({ ...signupForm, school_email: e.target.value })
                                        }
                                        placeholder="name@csu.fullerton.edu"
                                        className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-blue-500"
                                    />
                                </div>

                                <div>
                                    <label className="mb-2 block text-sm font-medium text-slate-700">Contact Email</label>
                                    <input
                                        type="email"
                                        value={signupForm.contact_email}
                                        onChange={(e) =>
                                            setSignupForm({ ...signupForm, contact_email: e.target.value })
                                        }
                                        placeholder="Optional, blank uses school email"
                                        className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-blue-500"
                                    />
                                </div>

                                <div>
                                    <label className="mb-2 block text-sm font-medium text-slate-700">Phone Number</label>
                                    <input
                                        type="text"
                                        value={signupForm.phone_number}
                                        onChange={(e) =>
                                            setSignupForm({ ...signupForm, phone_number: e.target.value })
                                        }
                                        placeholder="+1(###)-###-####"
                                        className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-blue-500"
                                    />
                                </div>

                                <div className="flex items-center gap-2 text-sm text-slate-600">
                                    <input
                                        type="checkbox"
                                        checked={signupForm.dsl_status}
                                        onChange={(e) =>
                                            setSignupForm({ ...signupForm, dsl_status: e.target.checked })
                                        }
                                    />
                                    DSL Student
                                </div>

                                <div>
                                    <label className="mb-2 block text-sm font-medium text-slate-700">Password</label>
                                    <input
                                        type="password"
                                        value={signupForm.password}
                                        onChange={(e) =>
                                            setSignupForm({ ...signupForm, password: e.target.value })
                                        }
                                        placeholder="Create a password"
                                        className="w-full rounded-2xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-blue-500"
                                    />
                                </div>

                                <button
                                    type="submit"
                                    className="w-full rounded-2xl bg-blue-600 px-5 py-3 text-sm font-medium text-white shadow-sm hover:bg-blue-700"
                                >
                                    Create Account
                                </button>
                            </form>
                        )}

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