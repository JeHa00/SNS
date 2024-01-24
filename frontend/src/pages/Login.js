import styled from "styled-components/macro";
import { Link } from "react-router-dom";
import logo from "../logo_img/logo.png";

const LoginBlock = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
`;
const LoginForm = styled.form`
  width: 300px;
  height: 300px;
  display: flex;
  flex-direction: column;
  align-items: center;
  input:focus {
    outline: 1px solid green;
  }
`;

const Logo = styled.img`
  width: 280px;
`;

function Login() {
  return (
    <LoginBlock>
      <Logo src={logo} />
      <LoginForm>
        <div>
          <label for='email'>이메일</label>
          <input id='email'></input>
        </div>
        <div>
          <label for='pasword'>비밀번호</label>
          <input id='pasword'></input>
        </div>
        <Link to='/main'>
          <button>로그인</button>
        </Link>
        <Link to='/signup'>
          <button>회원가입</button>
        </Link>
      </LoginForm>
      <Link to='/reset-password'>
        <div>비밀번호를 잊으셨나요?</div>
      </Link>
    </LoginBlock>
  );
}

export default Login;
