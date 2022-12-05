from sso.account_structure import AccountStructure


class TestAccountStructure:

    __account_structure_raw = {
        "Accounts": [
            {
                "Id": "123456789012",
                "Arn": "arn:aws:organizations::012345678901:account/o-g1h2nv345q/123456789012",
                "Email": "awsdevelopment@example.com",
                "Name": "awsdevelopment@example.com",
                "Status": "ACTIVE",
                "JoinedMethod": "INVITED",
                "JoinedTimestamp": "2017-03-02 19:04:31.312000+00:00",
                "name_path": "/Root/Development",
                "id_path": "/r-abcd/ou-abcd-scf1ga23",
            },
        ]
    }

    def test_account_structure(self):

        account_structure = AccountStructure(TestAccountStructure.__account_structure_raw)

        acc = account_structure.account_structure

        assert "Accounts" in acc

    def test_accounts(self):

        account_structure = AccountStructure(TestAccountStructure.__account_structure_raw)

        for account in account_structure.accounts:
            assert account["Id"] == "123456789012"
            assert account["name_path"] == "/Root/Development"
            assert account["id_path"] == "/r-abcd/ou-abcd-scf1ga23"
