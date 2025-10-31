from crossclient import CrossClient, submit_results

if __name__ == "__main__":
    client = CrossClient(
        username="jabmin",
        password="jabmin_password",
        base_url="http://localhost/api/v1",
    )
    fn_csv = (
        "E:/GIT/cross_back/add_initial_data/data/results/resultsCross_SES_stacked.csv"
    )
    fn_excel = "E:/GIT/cross_back/add_initial_data/data/results/resultsCross_SES.xlsx"
    submit_results(
        client=client,
        fn_results=fn_csv,
        df_results=None,
        submission_contract=None,
    )
    submit_results(
        client=client,
        fn_results=fn_excel,
        df_results=None,
        submission_contract=None,
    )
