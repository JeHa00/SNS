import { Suspense, lazy } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { createGlobalStyle, styled } from "styled-components/macro";
import reset from "styled-reset";

const GlobalStyles = createGlobalStyle`
  ${reset}
  body{
    box-sizing: border-box;
    display: flex;
    justify-content: center;
  }
  input{
        outline: 0;
  }
`;

const Container = styled.div`
  height: 100vh;
  width: 390px; //고민...
  border: 1px solid black;
  display: flex;
  justify-content: center;
  align-items: center;
`;

const Login = lazy(() => import("./pages/Login"));

function App() {
  return (
    <BrowserRouter>
      <Suspense fallback='로딩중'>
        <GlobalStyles />
        <div className='App'>
          <Container>
            <Routes>
              <Route path='/' element={<Login />}></Route>
            </Routes>
          </Container>
        </div>
      </Suspense>
    </BrowserRouter>
  );
}

export default App;
