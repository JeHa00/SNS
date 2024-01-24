import { Link, useNavigate } from "react-router-dom";
import styled from "styled-components/macro";
import { MdFoodBank } from "react-icons/md";
import {
  IoChevronBack,
  IoNotifications,
  IoPersonCircleOutline,
} from "react-icons/io5";
import Logo_name from "../logo_img/logo_name.png";

const HeaderBlock = styled.div`
  background-color: #11c559;
  height: 70px;
  position: fixed;
  top: 0;
  width: 390px;
  display: flex;
  div {
    display: flex;
    align-items: center;
    justify-content: end;
    width: 100px;
  }
  .feed-arrow {
    justify-content: flex-start;
  }
  .logo {
    width: 200px;
  }
`;

const LogoName = styled.img`
  width: 200px;
`;

const Feed = styled(MdFoodBank)`
  color: white;
  margin: 5px;
`;

const BackArrow = styled(IoChevronBack)`
  color: white;
  margin: 5px;
`;

const Noti = styled(IoNotifications)`
  color: white;
  margin-right: 6.5px;
`;

const Mypage = styled(IoPersonCircleOutline)`
  color: white;
  margin-right: 6.5px;
`;

function Header({
  menuHandler,
  feed = true,
  logo = true,
  noti = true,
  mypage = true,
  scroll = false,
}) {
  const navigate = useNavigate();
  const scrollHandler = () => {
    if (scroll) {
      navigate("/main"); //뒤로가기 만들면 필요 없을듯? 고민..
      window.scrollTo(0, 0);
    }
  };
  return (
    <HeaderBlock>
      <div className='feed-arrow'>
        {feed ? (
          <Link to='/feedinfo'>
            <Feed size='35' />
          </Link>
        ) : (
          <BackArrow size='30' onClick={menuHandler} />
        )}
      </div>
      <div className='logo'>
        <LogoName src={Logo_name} onClick={scrollHandler} />
      </div>
      <div>
        {noti ? <Noti size='25' /> : null}
        {mypage ? (
          <Link to='/userfeed'>
            <Mypage size='29' />
          </Link>
        ) : null}
      </div>
    </HeaderBlock>
  );
}

export default Header;
