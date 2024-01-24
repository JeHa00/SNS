import { Suspense, lazy } from "react";
import { Link, Route, Routes } from "react-router-dom";
import styled from "styled-components/macro";
import { BsSearch } from "react-icons/bs";

const SearchBlock = styled.div`
  display: flex;
  align-items: center;
`;
const SearchInput = styled.input`
  width: 310px;
  height: 35px;
  border: 2px solid #11c559;
  border-radius: 4px;
  margin: 20px 12px 14px 20px;
`;

const SearchIcon = styled(BsSearch)`
  width: 30px;
  height: 30px;
  color: #11c559;
  cursor: pointer;
  margin: 20px 18px 15px 0px;
  &:hover {
    color: #123b77;
  }
`;

function Search() {
  return (
    <SearchBlock>
      <SearchInput />
      <SearchIcon />
    </SearchBlock>
  );
}

export default Search;
