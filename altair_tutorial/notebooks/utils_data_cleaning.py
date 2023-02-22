from datetime import datetime
from bs4 import BeautifulSoup as bs
import re
import pandas as pd
import numpy as np
import os
from pathlib import Path

############################################################################
############################################################################

## Function to end-to-end parse the filings and write to a pandas dataframe

def end_to_end_parsing(file_path, directory_parquet):
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

                portfolioDict["securityType"] = row.find("sshPrnamtType").text.strip()

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
                        "securityType": "",
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

    data.insert(
        0,
        "ID",
        data.accessionNumber.map(str)
        + "-"
        + data.cikManager.map(str)
        + "-"
        + data.index.map(str),
    )

    column_names = [
        "ID",
        "accessionNumber",
        "cikManager",
        "managerName",
        "periodOfReport",
        "report_Quarter",
        "report_Year",
        "submissionType",
        "filedAsOfDate",
        "isAmendment",
        "amendmentType",
        "entryTotal",
        "valueTotal",
        "cusip",
        "nameOfIssuer",
        "titleOfClass",
        "sharesValue",
        "sharesHeldAtEndOfQtr",
        "sharePriceAtEndOfQtr",
        "securityType",
        "putCall",
        "xml_flag",
        "created_at",
        "edgar_path",
    ]
    data = data.astype(
        {
            "ID": str,
            "accessionNumber": str,
            "cikManager": "Int64",
            "periodOfReport": "datetime64[ns]",
            "report_Quarter": "Int64",
            "report_Year": "Int64",
            "submissionType": str,
            "isAmendment": bool,
            "amendmentType": str,
            "filedAsOfDate": "datetime64[ns]",
            "entryTotal": "Int64",
            "valueTotal": "float64",
            "cusip": str,
            "nameOfIssuer": str,
            "titleOfClass": str,
            "sharesValue": "float64",
            "sharesHeldAtEndOfQtr": "Int64",
            "securityType": str,
            "putCall": str,
            "xml_flag": str,
            "created_at": "datetime64[ns]",
            "edgar_path": str,
        }
    )
    data = data.assign(cusip=data.cusip.str.upper())
    data = data.reindex(columns=column_names)
    
    attributes = {
        "ID": "first",
        "accessionNumber": "first",
        "cikManager": "first",
        "managerName": "first",
        "periodOfReport": "first",
        "report_Quarter": "first",
        "report_Year": "first",
        "submissionType": "first",
        "filedAsOfDate": "first",
        "isAmendment": "first",
        "amendmentType": "first",
        "entryTotal": "first",
        "valueTotal": "first",
        "cusip": "first",
        "nameOfIssuer": "first",
        "titleOfClass": "first",
        "sharesValue": "sum",
        "sharesHeldAtEndOfQtr": "sum",
        "securityType": "first",
        "putCall": "first",
        "xml_flag": "first",
        "created_at": "first",
        "edgar_path": "first",
    }
    
    df2 = data.groupby(["cusip"], as_index=False).agg(attributes)
    df2.to_parquet(
        os.path.join(
            directory_parquet,
            f"{df2.head(1).cikManager[0]}-{df2.head(1).accessionNumber[0]}-{df2.head(1).filedAsOfDate[0].strftime('%Y-%m-%d')}.parquet",
        )
    )
    

    return df2
           
            
            
if __name__ == "__main__":
    end_to_end_parsing(file, directory_parq)
