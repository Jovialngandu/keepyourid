import { BrowserRouter, Routes, Route } from "react-router-dom";

import Home from "./pages/Home";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Organizations from "./pages/Organizations";
import OrganizationRegister from "./pages/OrganizationRegister";
import OrganizationDashboard from "./pages/OrganizationDashboard";
import DIDSetup from "./pages/DIDSetup";
import IssueCredential from "./pages/IssueCredential";
import CredentialDetails from "./pages/CredentialDetails";
import CredentialCreate from "./pages/CredentialCreate";
import Credentials from "./pages/Credentials";
import Wallet from "./pages/Wallet";
import Verify from "./pages/Verify";

import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/auth/ProtectedRoute";

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/verify" element={<Verify />} />

          <Route element={<ProtectedRoute />}>
            <Route path="/organizations" element={<Organizations />} />
            <Route path="/organizations/new" element={<OrganizationRegister />} />
            <Route
              path="/organizations/:organizationId"
              element={<OrganizationDashboard />}
            />
            <Route
              path="/organizations/:organizationId/identity"
              element={<DIDSetup />}

            />


<Route
  path="/organizations/:organizationId/credentials"
  element={<Credentials />}
/>

<Route
  path="/organizations/:organizationId/credentials/:credentialId"
  element={<CredentialDetails />}
/>


<Route path="/wallet" element={<Wallet />} />

			<Route path="/organizations" element={<Organizations />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;