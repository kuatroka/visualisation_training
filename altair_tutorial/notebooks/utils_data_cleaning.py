from datetime import datetime
from bs4 import BeautifulSoup as bs
import re
import pandas as pd
import numpy as np
import os
from pathlib import Path
import pandera as pa

############################################################################
############################################################################

## Function to end-to-end parse the filings and write to a pandas dataframe
# no division by 1000
# cusip transformed to upper case

# !! TODO !! add the removal of records with zeros/nan in shares/value, non-9 cusip, non-xml filings, add column for 'dsource' = sec_app
# rename column to a common standard with dropbox

def end_to_end_parsing(file_path, directory_parquet, failures_parq_dir):
    """
    func that takes a txt filing's path and parses it to a parquet file
    in the `directory_parquet`. It uses `pandera` lazy mode to filter out
    bad cusip or empty/nan/zero shares or values. Bad records are written
    to the `failures_parq_dir` for a later analysis or correction.
    
    """
    def work_content_extract(file_path):
        """extracting 1. xml or not flag, 2. xml part of filings, SEC header part"""
        open_file = open(file_path, "r")
        file_content = open_file.read()
        open_file.close()

        # find block of text between two words/tags/strings
        start_header = "<SEC-HEADER>"
        end_header = "</SEC-HEADER>"
        block_header_search = re.compile(f"{start_header}.*?{end_header}", re.DOTALL)
        pages_header = re.findall(block_header_search, file_content)

        # check if file is XML or not
        xml_tag_search = re.compile(r"<xml>", flags=re.IGNORECASE)
        if xml_tag_search.search(file_content):
            xml_flag = "YES"

            # xml block search
            start_xml = "<XML\>"
            end_xml = "<\/XML\>"
            block_xml_search = re.compile(f"{start_xml}(.*?){end_xml}", re.DOTALL)
            pages_xml = re.findall(block_xml_search, file_content)

            if len(pages_xml) == 0:
                reportType = ""
                document0 = ""
                document1 = ""
            elif len(pages_xml) == 1:
                document0 = bs(pages_xml[0], "xml")
                coverPage = document0.find("coverPage")
                reportType = coverPage.find("reportType").text.strip()
                document1 = ""
            if len(pages_xml) > 1:
                document0 = bs(pages_xml[0], "xml")
                coverPage = document0.find("coverPage")
                reportType = coverPage.find("reportType").text.strip()
                document1 = bs(pages_xml[1], "xml")

        else:
            xml_flag = "NO"
            pages_xml = []
            reportType = ""
            document1 = ""

        return pages_header, pages_xml, xml_flag, reportType, document1

    def parse_institutionalInvestorInfo(file_path):
        dataDictionary = dict()
        dataDictionary["edgar_path"] = file_path
        periodOfReport = datetime.strptime(
            re.compile(r"(?<=CONFORMED PERIOD OF REPORT:).*")
            .search(pages_header[0])
            .group(0)
            .strip(),
            "%Y%m%d",
        ).date()
        report_Year, report_Quarter = (
            periodOfReport.year,
            (periodOfReport.month - 1) // 3 + 1,
        )

        dataDictionary["accessionNumber"] = (
            re.compile(r"(?<=ACCESSION NUMBER:).*")
            .search(pages_header[0])
            .group(0)
            .strip()
        )
        dataDictionary["cikManager"] = (
            re.compile(r"(?<=CENTRAL INDEX KEY:).*")
            .search(pages_header[0])
            .group(0)
            .strip()
        )
        dataDictionary["managerName"] = (
            re.compile(r"(?<=COMPANY CONFORMED NAME:).*")
            .search(pages_header[0])
            .group(0)
            .strip()
        )
        dataDictionary["periodOfReport"] = periodOfReport
        dataDictionary["report_Quarter"] = report_Quarter
        dataDictionary["report_Year"] = report_Year
        dataDictionary["submissionType"] = (
            re.compile(r"(?<=CONFORMED SUBMISSION TYPE:).*")
            .search(pages_header[0])
            .group(0)
            .strip()
        )
        dataDictionary["filedAsOfDate"] = datetime.strptime(
            re.compile(r"(?<=FILED AS OF DATE:).*")
            .search(pages_header[0])
            .group(0)
            .strip(),
            "%Y%m%d",
        ).date()
        dataDictionary["xml_flag"] = xml_flag
        dataDictionary["created_at"] = datetime.now()

        # dataDictionary = dict()
        dataDictionary["edgar_path"] = file_path
        if xml_flag == "NO":

            dataDictionary["isAmendment"] = ""
            dataDictionary["amendmentType"] = ""
            dataDictionary["entryTotal"] = int("0" + "")
            dataDictionary["valueTotal"] = float("0.0" + "")
            dt = pd.DataFrame.from_dict([dataDictionary])

        else:
            if len(pages_xml) == 0:
                dataDictionary["isAmendment"] = ""
                dataDictionary["amendmentType"] = ""
                dataDictionary["entryTotal"] = int("0" + "")
                dataDictionary["valueTotal"] = float("0.0" + "")
                dt = pd.DataFrame.from_dict([dataDictionary])

            else:
                document = bs(pages_xml[0], "xml")
                # get sections
                coverPage = document.find("coverPage")
                summaryPage = document.find("summaryPage")
                # get data
                if coverPage.find("isAmendment") is not None:

                    if coverPage.find("isAmendment").text.strip() == "true":
                        dataDictionary["isAmendment"] = coverPage.find(
                            "isAmendment"
                        ).text.strip()
                        if coverPage.find("amendmentType"):
                            dataDictionary["amendmentType"] = coverPage.find(
                                "amendmentType"
                            ).text.strip()
                        else:
                            dataDictionary["amendmentType"] = ""
                    else:
                        dataDictionary["isAmendment"] = coverPage.find(
                            "isAmendment"
                        ).text.strip()
                        dataDictionary["amendmentType"] = ""
                else:
                    dataDictionary["isAmendment"] = ""
                    dataDictionary["amendmentType"] = ""

                if summaryPage is not None:
                    if summaryPage.find("tableEntryTotal").text.strip():
                        dataDictionary["entryTotal"] = int(
                            float(summaryPage.find("tableEntryTotal").text.strip() + "0.0")
                        )
                    else:
                        dataDictionary["entryTotal"] = int("0" + "")


                    if summaryPage.find("tableValueTotal").text.strip():
                        dataDictionary["valueTotal"] = float(
                        summaryPage.find("tableValueTotal").text.strip()
                    + "0.0")

                    else: dataDictionary["valueTotal"] = float("0.0" + "")
                else:
                    dataDictionary["entryTotal"], dataDictionary["valueTotal"] = int(
                        "0" + ""
                    ), float("0.0" + "")

                # create dataframe
                dt = pd.DataFrame.from_dict([dataDictionary])

        return dt

    def parse_institutionalInvestorPortfolio(file_path):
        check = re.compile("13F HOLDINGS REPORT|13F COMBINATION REPORT")
        if check.search(reportType) is not None and len(pages_xml) > 1:

            portfolio = list()
            # find all securities held

            securities = document1.find_all("infoTable")
            for row in securities:
                portfolioDict = dict()
                portfolioDict["edgar_path"] = file_path
                portfolioDict["cusip"] = row.find("cusip").text.strip()
                portfolioDict["nameOfIssuer"] = row.find("nameOfIssuer").text.strip()
                portfolioDict["titleOfClass"] = row.find("titleOfClass").text.strip()
                portfolioDict["sharesValue"] = float(
                    row.find("value").text.strip()
                )
                portfolioDict["sharesHeldAtEndOfQtr"] = int(
                    float(row.find("sshPrnamt").text.strip())
                )

                try:
                    portfolioDict["sharePriceAtEndOfQtr"] = round(
                        portfolioDict["sharesValue"]
                        / portfolioDict["sharesHeldAtEndOfQtr"],
                        2,
                    )
                except ZeroDivisionError:
                    portfolioDict["sharePriceAtEndOfQtr"] = float(int("0" + ""))

                portfolioDict["shares_bonds"] = row.find("sshPrnamtType").text.strip()

                if row.find("putCall") is not None:
                    portfolioDict["putCall"] = row.find("putCall").text.strip()
                else:
                    portfolioDict["putCall"] = ""

                portfolio.append(pd.DataFrame.from_dict([portfolioDict]))

            # concatanate secutires
            dtPortfolio = pd.concat(portfolio, sort=False, ignore_index=True)
        else:
            dtPortfolio = pd.DataFrame.from_dict(
                [
                    {
                        "cusip": "",
                        "nameOfIssuer": "",
                        "titleOfClass": "",
                        "sharesValue": float("0.0" + ""),
                        "sharesHeldAtEndOfQtr": int("0" + ""),
                        "sharePriceAtEndOfQtr": float("0.0" + ""),
                        "shares_bonds": "",
                        "putCall": "",
                        "edgar_path": file_path,
                    }
                ]
            )

        return dtPortfolio

    pages_header, pages_xml, xml_flag, reportType, document1 = work_content_extract(
        file_path
    )
    df1, df2 = parse_institutionalInvestorInfo(
        file_path
    ), parse_institutionalInvestorPortfolio(file_path)

    data = pd.merge(df1, df2, on="edgar_path")
    data = data.assign(dsource='sec_app')    
    data = data.rename(columns={'accessionNumber': 'accession_number', "cikManager": 'cik', "managerName":'cik_name','xml_flag':'type',
           "periodOfReport": 'rdate', "submissionType": 'submission_type', "filedAsOfDate":'fdate', "entryTotal": "entry_total",
           "valueTotal": "value_total", 'putCall':'put_call', "sharesValue":'value', "sharesHeldAtEndOfQtr":'shares',
           "securityType": "security_type", 'titleOfClass':'title_of_class', 'nameOfIssuer':'name_of_issuer' , "edgar_path":'file'})

    column_names = [
        "accession_number",
        "cik",
        "cik_name",
        "rdate",
        "submission_type",
        "fdate",
        "entry_total",
        "value_total",
        "cusip",
        "name_of_issuer",
        "title_of_class",
        "value",
        "shares",
        "shares_bonds",
        "put_call",
        "type",
        "created_at",
        "file",
        'dsource'
    ]
    data = data.astype(
        {
            "accession_number": str,
            "cik": "Int64",
            'cik_name': str,
            "rdate": "datetime64[ns]",
            "submission_type": str,
            "fdate": "datetime64[ns]",
            "entry_total": "Int64",
            "value_total": "float64",
            "cusip": str,
            "name_of_issuer": str,
            "title_of_class": str,
            "value": "float64",
            "shares": "float64",
            "shares_bonds": str,
            "put_call": str,
            "type": str,
            "created_at": "datetime64[ns]",
            "file": str,
            'dsource': str
        }
    )
    attributes = {
        "accession_number": "first",
        "cik": "first",
        "cik_name": "first",
        "rdate": "first",
        "submission_type": "first",
        "fdate": "first",
        "entry_total": "first",
        "value_total": "first",
        "cusip": "first",
        "name_of_issuer": "first",
        "title_of_class": "first",
        "value": "sum",
        "shares": "sum",
        "shares_bonds": "first",
        "put_call": "first",
        "type": "first",
        "file": "first",
        'dsource': 'first'
    }
    data = data.assign(cusip=data.cusip.str.upper())
    data = data.reindex(columns=column_names)
   
    ## pandera code
    validation_schema = pa.DataFrameSchema({
    "cusip": pa.Column(str,
                       pa.Check(lambda s: s.str.len() == 9),
                       required=True, nullable=False),
    "value":  pa.Column(float, pa.Check(lambda s: s != 0.0), required=True, nullable=False),
    "shares": pa.Column(float, pa.Check(lambda s: s != 0.0), required=True, nullable=False)
        })
    if data.head(1).type.squeeze() != 'NO':
        try:
            validation_schema.validate(data, lazy=True)
            if not data.empty:
                # group cusips
                df2 = data.groupby(["cusip"], as_index=False).agg(attributes)
                df2.to_parquet(
                    os.path.join(
                        directory_parquet,
                        f"{df2.head(1).cik[0]}-{df2.head(1).accession_number[0]}-{df2.head(1).fdate[0].strftime('%Y-%m-%d')}.parquet",
                                    )
                                )

                # return df2
            else: pd.DataFrame()

        except pa.errors.SchemaErrors as e:
            failure_cases = e.failure_cases
            failure_cases = (failure_cases.assign(df_file=data.file,
                                                 df_cik=data.cik,
                                                 df_rdate=data.rdate,
                                                 df_fdate=data.fdate,
                                                 df_value=data.value)).astype({'failure_case':str})
            # print(failure_cases)
            failure_cases.to_parquet(Path.joinpath(failures_parq_dir, \
                                                   f"bad-{data.head(1).cik[0]}-{data.head(1).accession_number[0]}-   {data.head(1).fdate[0].strftime('%Y-%m-%d')}.parquet"))
            data = data[~data.index.isin(failure_cases["index"])]
            if not data.empty:
                # group cusips
                df2 = data.groupby(["cusip"], as_index=False).agg(attributes)
                df2.to_parquet(
                    os.path.join(
                        directory_parquet,
                        f"{df2.head(1).cik[0]}-{df2.head(1).accession_number[0]}-{df2.head(1).fdate[0].strftime('%Y-%m-%d')}.parquet",
                                    )
                                )

                # return df2
            else: pd.DataFrame()
            
            
if __name__ == "__main__":
    end_to_end_parsing(file, directory_parq, failure_dir)
