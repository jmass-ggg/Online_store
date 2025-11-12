import SignUp from "./components/SignUp";
import Login from "./components/Login";
import Homepage from "./components/Homepage";
import OrderConfirmation from "./components/OrderConfirmation"; // ✅ added this import
import { Route, Switch, Redirect } from "react-router-dom";

// Private route for logged-in users
const PrivateRoute = ({ component: Component, ...rest }) => {
  return (
    <Route
      {...rest}
      render={(props) => {
        const token = localStorage.getItem("token");
        if (!token) {
          return <Redirect to="/login" />;
        }
        return <Component {...props} />;
      }}
    />
  );
};

function App() {
  return (
    <Switch>
      <Route path="/login" component={Login} />
      <Route path="/signup" component={SignUp} />
      <PrivateRoute path="/homepage" component={Homepage} />
      <PrivateRoute
        path="/order-confirmation/:id"
        component={OrderConfirmation} // ✅ added this route
      />
      <Redirect from="/" to="/login" />
    </Switch>
  );
}

export default App;
