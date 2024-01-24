import { Suspense, lazy } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { createGlobalStyle, styled } from "styled-components/macro";
import reset from "styled-reset";

const GlobalStyles = createGlobalStyle`
  ${reset}
  *{
    box-sizing: border-box;
  }
  body{
    display: flex;
    justify-content: center;
    // 드래그 방지
    -webkit-user-select:none;
    -moz-user-select:none;
    -ms-user-select:none;
    user-select:none;
    color: #2D2D2D;
  }
  input{
    outline: 0;
  }
  a{
    text-decoration: none;
    color: inherit;
  }
`;

const Container = styled.div`
  width: 390px; //고민...
  height: 100vh; // 높이 부분이 스크롤 하면 해결이 안되데..
  border: 0.5px solid black;
  padding-top: 70px;
`;

const Login = lazy(() => import("./pages/Login"));
const Signup = lazy(() => import("./pages/Signup"));
const Main = lazy(() => import("./pages/Main"));
const UserFeed = lazy(() => import("./pages/UserFeed"));
const EditProfile = lazy(() => import("./pages/EditProfile"));
const ChangePassword = lazy(() => import("./pages/ChangePassword"));
const ResetPassword = lazy(() => import("./pages/ResetPassword"));
const FollowLists = lazy(() => import("./pages/FollowLists"));
const LodingIcon = lazy(() => import("./components/LodingIcon"));
const FeedInfo = lazy(() => import("./pages/FeedInfo"));

function App() {
  return (
    <BrowserRouter>
      <GlobalStyles />
      <div className='App'>
        <Container>
          <Suspense fallback={<LodingIcon />}>
            <Routes>
              <Route path='/' element={<Login />} />
              <Route path='/signup' element={<Signup />} />
              <Route path='/main' element={<Main />} />
              <Route path='/userfeed' element={<UserFeed />} />
              <Route path='/edit-profile' element={<EditProfile />} />
              <Route path='/change-password' element={<ChangePassword />} />
              <Route path='/reset-password' element={<ResetPassword />} />
              <Route path='/follow-lists/*' element={<FollowLists />} />
              <Route path='/feedinfo' element={<FeedInfo />} />
            </Routes>
          </Suspense>
        </Container>
      </div>
    </BrowserRouter>
  );
}

export default App;
