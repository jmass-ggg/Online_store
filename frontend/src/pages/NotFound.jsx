import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <div style={{ maxWidth: 700, margin: "40px auto", padding: 20 }}>
      <h1>Page Not Found</h1>
      <p>The route you opened does not exist.</p>
      <Link to="/">Go Home</Link>
    </div>
  );
}