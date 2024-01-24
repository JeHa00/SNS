import styled from "styled-components/macro";
import Post from "../components/Post";
import Header from "../components/Header";
import Search from "../components/Search";
import { useState } from "react";

const MainBlock = styled.main`
  overflow: auto;
`;
const FilterBlock = styled.div`
  display: flex;
  margin: 6px 20px 0px 20px;
  span {
    margin-right: 5px;
  }
  .green {
    color: #11c559;
  }
  .pointer {
    cursor: pointer;
  }
`;

function Main() {
  const [clickFilter, setClickFilter] = useState(true);

  const checkAllFilter = () => {
    setClickFilter(true);
  };
  const checkFollowFilter = () => {
    setClickFilter(false);
  };
  return (
    <div>
      <Header scroll={true} />
      <MainBlock>
        <Search />
        <FilterBlock>
          <span
            className={clickFilter ? "green pointer" : "pointer"}
            onClick={checkAllFilter}
          >
            전체
          </span>
          <span>|</span>
          <span
            className={clickFilter ? "pointer" : "green pointer"}
            onClick={checkFollowFilter}
          >
            팔로우
          </span>
        </FilterBlock>
        <Post />
        <Post />
        <Post />
        <Post />
        <Post />
        <Post />
        <Post />
        <Post />
        <Post />
        <Post />
        <Post />
      </MainBlock>
    </div>
  );
}

export default Main;
